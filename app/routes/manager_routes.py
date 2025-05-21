from flask import Blueprint, render_template, redirect, url_for, flash, request
from bookstore_flask_project.app import db
from bookstore_flask_project.app.models import Book, User, Order
from bookstore_flask_project.app.forms import BookForm  # You might need UserForm, OrderStatusForm etc.
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime

bp = Blueprint('manager', __name__)


# Decorator to check if user is a manager
def manager_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'manager':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('customer.index'))
        return f(*args, **kwargs)

    return decorated_function


@bp.route('/dashboard')
@manager_required
def dashboard():
    # Placeholder: Fetch some stats for the dashboard
    total_books = Book.query.count()
    total_users = User.query.count()
    pending_orders = Order.query.filter_by(status='pending_payment').count()  # Or other relevant status
    return render_template('manager/dashboard.html',
                           title='Manager Dashboard',
                           total_books=total_books,
                           total_users=total_users,
                           pending_orders=pending_orders)


@bp.route('/books')
@manager_required
def list_books():
    page = request.args.get('page', 1, type=int)
    books_pagination = Book.query.order_by(Book.title.asc()).paginate(page=page, per_page=10, error_out=False)
    books = books_pagination.items
    return render_template('manager/manage_books.html', title='Manage Books', books=books, pagination=books_pagination)


@bp.route('/books/add', methods=['GET', 'POST'])
@manager_required
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        filename = None
        if form.cover_image.data:
            # Handle file upload
            # Ensure FLASK_APP_INSTANCE_PATH/uploads directory exists
            # from your app instance folder (e.g., bookstore_flask_project/instance/uploads)
            # You need to configure UPLOAD_FOLDER in config.py
            # app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
            # and ensure it's created.
            # For simplicity, we'll just store the filename.
            # In a real app, save the file securely.
            f = form.cover_image.data
            filename = secure_filename(f.filename)
            # Example: f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            # For now, let's assume you store it and just save the name.
            # You'd need to create the 'uploads' folder in 'instance' directory.
            # Ensure UPLOAD_FOLDER is defined in your config.py and app/__init__.py loads it.

        pub_date = None
        if form.publication_date.data:
            try:
                pub_date = datetime.strptime(form.publication_date.data, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid publication date format. Please use YYYY-MM-DD.', 'danger')
                return render_template('manager/add_edit_book.html', title='Add New Book', form=form, action='Add')

        new_book = Book(
            title=form.title.data,
            author=form.author.data,
            isbn=form.isbn.data,
            description=form.description.data,
            price=form.price.data,
            stock_quantity=form.stock_quantity.data,
            cover_image_filename=filename,  # Store filename
            category=form.category.data,
            publication_date=pub_date
        )
        db.session.add(new_book)
        db.session.commit()
        flash(f"Book '{new_book.title}' added successfully!", 'success')
        return redirect(url_for('manager.list_books'))
    elif request.method == 'POST':  # Form validation failed
        flash('Please correct the errors below.', 'danger')

    return render_template('manager/add_edit_book.html', title='Add New Book', form=form, action='Add')


@bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@manager_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)  # Pre-populate form with book data

    if form.validate_on_submit():
        # Handle file upload for cover image if a new one is provided
        if form.cover_image.data:
            f = form.cover_image.data
            new_filename = secure_filename(f.filename)
            # Save new file, potentially delete old one
            # Example: f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename))
            book.cover_image_filename = new_filename

        pub_date = book.publication_date  # Keep existing if not changed
        if form.publication_date.data:
            try:
                # Ensure data is a string before strptime
                date_str = form.publication_date.data
                if isinstance(date_str, datetime):  # If it's already a datetime object
                    pub_date = date_str.date()
                elif isinstance(date_str, str):
                    pub_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid publication date format. Please use YYYY-MM-DD.', 'danger')
                return render_template('manager/add_edit_book.html', title=f'Edit Book: {book.title}', form=form,
                                       book=book, action='Edit')

        book.title = form.title.data
        book.author = form.author.data
        book.isbn = form.isbn.data
        book.description = form.description.data
        book.price = form.price.data
        book.stock_quantity = form.stock_quantity.data
        book.category = form.category.data
        book.publication_date = pub_date

        db.session.commit()
        flash(f"Book '{book.title}' updated successfully!", 'success')
        return redirect(url_for('manager.list_books'))
    elif request.method == 'POST':  # Form validation failed
        flash('Please correct the errors below.', 'danger')

    # Pre-fill publication_date if it exists
    if book.publication_date:
        form.publication_date.data = book.publication_date.strftime('%Y-%m-%d')

    return render_template('manager/add_edit_book.html', title=f'Edit Book: {book.title}', form=form, book=book,
                           action='Edit')


@bp.route('/books/delete/<int:book_id>', methods=['POST'])  # Use POST for delete actions
@manager_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    # Potentially delete associated cover image file from filesystem here
    db.session.delete(book)
    db.session.commit()
    flash(f"Book '{book.title}' deleted successfully.", 'success')
    return redirect(url_for('manager.list_books'))


@bp.route('/users')
@manager_required
def list_users():
    page = request.args.get('page', 1, type=int)
    users_pagination = User.query.order_by(User.username.asc()).paginate(page=page, per_page=10, error_out=False)
    users = users_pagination.items
    return render_template('manager/manage_users.html', title='Manage Users', users=users, pagination=users_pagination)


@bp.route('/orders')
@manager_required
def list_orders():
    page = request.args.get('page', 1, type=int)
    orders_pagination = Order.query.order_by(Order.order_date.desc()).paginate(page=page, per_page=10, error_out=False)
    orders = orders_pagination.items
    return render_template('manager/manage_orders.html', title='Manage Orders', orders=orders,
                           pagination=orders_pagination)


@bp.route('/orders/view/<int:order_id>')
@manager_required
def view_order_detail_manager(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('manager/view_order_detail.html', title=f'Order #{order.id} Details', order=order)


@bp.route('/orders/update_status/<int:order_id>', methods=['POST'])
@manager_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    valid_statuses = ['pending_payment', 'processing', 'shipped', 'delivered', 'cancelled']  # Define your statuses
    if new_status in valid_statuses:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status}.', 'success')
    else:
        flash('Invalid status update.', 'danger')
    return redirect(url_for('manager.view_order_detail_manager', order_id=order.id))