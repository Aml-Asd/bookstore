from flask import Blueprint, render_template, redirect, url_for, flash, request
from bookstore_flask_project.app import db
from bookstore_flask_project.app.models import Book, CartItem, Order, OrderItem
from bookstore_flask_project.app.forms import AddToCartForm, UpdateCartItemForm

from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError  # For handling unique constraint violations

bp = Blueprint('customer', __name__)


@bp.route('/')
@bp.route('/index')
def index():
    # Placeholder: Fetch some books to display on the homepage
    featured_books = Book.query.order_by(Book.created_at.desc()).limit(6).all()
    new_arrivals = Book.query.order_by(Book.publication_date.desc()).limit(6).all()
    return render_template('customer/index.html',
                           title='Home',
                           featured_books=featured_books,
                           new_arrivals=new_arrivals)


@bp.route('/books')
def browse_books():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)

    query = Book.query
    if search_query:
        like_query = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Book.title.ilike(like_query),
                Book.author.ilike(like_query),
                Book.isbn.ilike(like_query),
                Book.category.ilike(like_query)
            )
        )

    books_pagination = query.order_by(Book.title.asc()).paginate(page=page, per_page=12, error_out=False)
    books = books_pagination.items

    return render_template('customer/browse_books.html',
                           title='Browse Books',
                           books=books,
                           pagination=books_pagination,
                           search_query=search_query)


@bp.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    form = AddToCartForm()  # For the "Add to Cart" button on the detail page
    return render_template('customer/book_detail.html', title=book.title, book=book, form=form)


@bp.route('/cart/add/<int:book_id>', methods=['POST'])
@login_required
def add_to_cart(book_id):
    book = Book.query.get_or_404(book_id)
    form = AddToCartForm()  # Process the submitted form

    if form.validate_on_submit():
        quantity = form.quantity.data
        if book.stock_quantity < quantity:
            flash(f"Sorry, only {book.stock_quantity} of '{book.title}' available in stock.", 'warning')
            return redirect(url_for('customer.book_detail', book_id=book_id))

        cart_item = CartItem.query.filter_by(user_id=current_user.id, book_id=book.id).first()
        if cart_item:
            # Check if adding more exceeds stock
            if book.stock_quantity < (cart_item.quantity + quantity):
                flash(
                    f"Cannot add {quantity} more. Only {book.stock_quantity - cart_item.quantity} additional items of '{book.title}' available.",
                    'warning')
                return redirect(request.referrer or url_for('customer.view_cart'))
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=current_user.id, book_id=book.id, quantity=quantity)
            db.session.add(cart_item)

        try:
            db.session.commit()
            flash(f"'{book.title}' (x{quantity}) added to your cart.", 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Could not add item to cart due to a database issue. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

    else:  # Form validation failed
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')

    return redirect(request.referrer or url_for('customer.view_cart'))


@bp.route('/cart')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_price = 0
    for item in cart_items:
        if item.book:  # Ensure book exists
            total_price += item.book.price * item.quantity

    update_form = UpdateCartItemForm()  # For each item in template
    return render_template('customer/cart.html', title='Your Cart', cart_items=cart_items, total_price=total_price,
                           update_form=update_form)


@bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart_item(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('You do not have permission to modify this item.', 'danger')
        return redirect(url_for('customer.view_cart'))

    form = UpdateCartItemForm()
    if form.validate_on_submit():
        new_quantity = form.quantity.data
        if new_quantity == 0:
            db.session.delete(cart_item)
            flash(f"'{cart_item.book.title}' removed from cart.", 'info')
        elif cart_item.book.stock_quantity < new_quantity:
            flash(
                f"Sorry, only {cart_item.book.stock_quantity} of '{cart_item.book.title}' available. Cart not updated.",
                'warning')
        else:
            cart_item.quantity = new_quantity
            flash(f"Quantity for '{cart_item.book.title}' updated.", 'success')
        db.session.commit()
    else:
        flash('Invalid quantity.', 'danger')
    return redirect(url_for('customer.view_cart'))


@bp.route('/cart/remove/<int:item_id>', methods=['POST'])  # Often done with POST for safety
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('You do not have permission to remove this item.', 'danger')
    else:
        book_title = cart_item.book.title if cart_item.book else "Item"
        db.session.delete(cart_item)
        db.session.commit()
        flash(f"'{book_title}' removed from your cart.", 'info')
    return redirect(url_for('customer.view_cart'))


@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty. Add some books before checking out!', 'info')
        return redirect(url_for('customer.browse_books'))

    total_price = sum(item.book.price * item.quantity for item in cart_items if item.book)

    # Simple form for shipping details (you'd use Flask-WTF for a real app)
    if request.method == 'POST':
        # In a real app, validate form data, process payment (mock for now)
        shipping_name = request.form.get('name')
        shipping_address1 = request.form.get('address1')
        # ... get other shipping fields

        # Check stock one last time
        for item in cart_items:
            if item.book.stock_quantity < item.quantity:
                flash(f"Sorry, '{item.book.title}' stock changed. Only {item.book.stock_quantity} available.",
                      'warning')
                return redirect(url_for('customer.view_cart'))

        # Create Order
        order = Order(
            user_id=current_user.id,
            total_amount=total_price,
            status='pending_payment',  # Or 'processing' if payment is mocked as successful
            shipping_name=shipping_name,
            shipping_address1=shipping_address1
            # ... set other shipping fields
        )
        db.session.add(order)
        db.session.flush()  # To get order.id for OrderItems

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                book_id=item.book_id,
                quantity=item.quantity,
                price_at_purchase=item.book.price
            )
            db.session.add(order_item)

            # Decrease stock
            item.book.stock_quantity -= item.quantity

            db.session.delete(item)  # Remove from cart

        db.session.commit()
        flash('Thank you for your order! It is being processed.', 'success')
        return redirect(url_for('customer.order_history'))  # Or an order confirmation page

    return render_template('customer/checkout.html', title='Checkout', cart_items=cart_items, total_price=total_price)


@bp.route('/orders')
@login_required
def order_history():
    page = request.args.get('page', 1, type=int)
    orders_pagination = Order.query.filter_by(user_id=current_user.id) \
        .order_by(Order.order_date.desc()) \
        .paginate(page=page, per_page=10, error_out=False)
    orders = orders_pagination.items
    return render_template('customer/order_history.html', title='My Orders', orders=orders,
                           pagination=orders_pagination)


@bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have permission to view this order.', 'danger')
        return redirect(url_for('customer.order_history'))
    return render_template('customer/order_detail.html', title=f'Order #{order.id}', order=order)