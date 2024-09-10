from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# If the user enters this as the account password, he/she is assigned the role of an administrator.
admin_password = 'placeholder_admin_password'

app = Flask(__name__, template_folder="templates")
app.config['SQLALCHEMY_DATABASE_URI'] = "your_db_uri"
db = SQLAlchemy(app)


# Creating models/tables


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30))
    password = db.Column(db.String(255))
    email = db.Column(db.String(50))
    phone_number = db.Column(db.String(10))
    address = db.Column(db.String(100))
    city = db.Column(db.String(40))
    pin_code = db.Column(db.String(6))
    is_admin = db.Column(db.Boolean)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(40))
    image = db.Column(db.String(60))
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)
    category = db.Column(db.String, db.ForeignKey('category.name'))
    best_before = db.Column(db.String(10))


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item = db.Column(db.String(40))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.Column(db.String(255))
    amount_paid = db.Column(db.Float)


# Database tables creation

with app.app_context():
    db.create_all()


# Welcome Page
@app.route('/')
def first_page():
    return render_template('first_page.html')


# Sign Up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    errors = []
    account_created = False

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        address = request.form.get('address')
        city = request.form.get('city')
        pin = request.form.get('pin')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_pw')

        # Input Validation
        if not all(char.isalpha() or char.isspace() for char in name):
            errors.append('Invalid name; only alphabetical characters allowed.')

        if not email.endswith(('@gmail.com', '@yahoo.com', '@yahoo.in')) or not email.replace('.', '').replace('@',
                                                                                                               '').isalnum():
            errors.append('Invalid email address.')

        else:
            user = User.query.filter_by(email=email).first()
            if user:
                errors.append('An account already exists with this email.')

        if not mobile.isdigit() or len(mobile) != 10:
            errors.append('Please provide a 10-digit phone number.')

        if not all(char.isalnum() or char in ('-', '.', '#', ',', ' ') for char in address):
            errors.append('Invalid address. Only alphanumeric characters, "-", ".", "#", and "," are allowed.')

        if not all(char.isalpha() or char.isspace() for char in city):
            errors.append('Invalid city; only alphabetical characters allowed.')

        if not pin.isdigit() or len(pin) != 6:
            errors.append('Please provide a 6-digit PIN Code.')

        if not all(char.isalnum() or char in ('!', '_', '?''#', '&') for char in password):
            errors.append(
                'Invalid password. Use only alphanumeric characters and/or special symbols !, _, ?, #, and &.')

        elif password != confirm_password:
            errors.append('Password and Confirm Password do not match.')

        if len(errors) == 0:
            is_admin = (password == admin_password)
            new_user = User(name=name, email=email, phone_number=mobile, address=address, city=city,
                            pin_code=pin, password=password, is_admin=is_admin)
            db.session.add(new_user)
            db.session.commit()
            account_created = True

    return render_template('signup.html', errors=errors, account_created=account_created)


# Log In
@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Input Validation
        if not email.endswith(('@gmail.com', '@yahoo.com', '@yahoo.in')) or not email.replace('.', '').replace('@',
                                                                                                               '').isalnum():
            error_message = 'Invalid email address entered.'

        else:
            user = User.query.filter_by(email=email).first()
            if not user:
                error_message = 'No account found with that email.'

            elif user.password != password:
                error_message = 'Incorrect password entered.'

        if error_message is not None:
            return render_template('login.html', error_message=error_message)

        else:
            user = User.query.filter_by(email=email).first()
            user_id = user.id
            return redirect(url_for('home', user_id=user_id))

    return render_template('login.html', error_message=error_message)


# Home Page; varies depending on whether the user is an administrator or not.
@app.route('/home/<int:user_id>')
def home(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user.is_admin:
        return redirect(url_for('admin_home'))
    else:
        return redirect(url_for('user_home', user_id=user_id))


# First page for the admin after logging in. Gives various options for inventory management.
@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html')


# First page for regular users. Displays products, and allows access to profile, cart and past orders.
@app.route('/user_home/<int:user_id>', methods=['GET', 'POST'])
def user_home(user_id):
    message = None
    message_colour = None

    user = User.query.filter_by(id=user_id).first()
    products = Product.query.order_by(Product.id.desc()).all()  # By default, all products are displayed.

    if request.method == 'POST':
        if 'search' in request.form:
            search_term = request.form.get('search')

            products = Product.query.filter(                            # Queries the products table for
                (Product.name.ilike(f'%{search_term}%')) |              # matches by name, or
                (Product.category.ilike(f'%{search_term}%'))            # matches by category, then
            ).order_by(Product.id.desc()).all()                         # prints them in descending order of ID.

            message = "Best matches for your search- "
            message_colour = 'black'

        elif 'add_product_name' in request.form:
            product_name = request.form.get('add_product_name')
            product_price = request.form.get('add_product_price')

            cart_item = Cart.query.filter_by(added_by=user.id, item=product_name).first()

            # Is the item already in the cart?
            if cart_item:
                product = Product.query.filter_by(name=cart_item.item).first()  # Yes, so query the products table
                if cart_item.quantity < product.stock:                          # and check the stock of that item;
                    cart_item.quantity += 1                                     # increase quantity only if possible
            else:
                cart_item = Cart(added_by=user.id, item=product_name, price=product_price, quantity=1)
                db.session.add(cart_item)  # No, so make a new entry to the cart.

            db.session.commit()

            message = 'The item has been added to your cart.'
            message_colour = 'green'

    return render_template('user_home.html', user=user, products=products,
                           message=message, message_colour=message_colour)


# User's profile; shows information entered while signing up.
@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.filter_by(id=user_id).first()
    return render_template('profile.html', user=user)


# User's cart; allows reduction in quantity, and complete removal, if needed.
@app.route('/cart/<int:user_id>', methods=['GET', 'POST'])
def cart(user_id):
    total_amount = 0
    messages = []
    user = User.query.filter_by(id=user_id).first()

    if request.method == 'POST':
        cart_items = Cart.query.filter_by(added_by=user_id).all()

        if 'reduce_product_name' in request.form:
            item_name = request.form.get('reduce_product_name')

            for item in cart_items:
                if item.item == item_name:
                    item.quantity -= 1                  # Reduce quantity by one, and
                    if item.quantity == 0:              # if quantity becomes zero,
                        cart_items.remove(item)         # remove the item from the cart.
                        db.session.delete(item)
                    db.session.commit()

        elif 'remove_product_name' in request.form:
            item_name = request.form.get('remove_product_name')

            for item in cart_items:
                if item.item == item_name:
                    cart_items.remove(item)  # Remove the item from the cart.
                    db.session.delete(item)
                    db.session.commit()

    else:
        cart_items = Cart.query.filter_by(added_by=user_id).all()

    if cart_items is not None:
        for item in cart_items:
            product = Product.query.filter_by(name=item.item).first()

            if product.stock >= item.quantity:
                total_amount += (item.price * item.quantity)

            elif product.stock > 0:
                item.quantity = product.stock  # Can't buy more than is available!
                db.session.commit()
                messages.append(
                    'Purchase of only ' + str(item.quantity) + ' of the item ' + item.item + ' will be possible. No '
                                                                                             'more stock left at '
                                                                                             'current time.')
                total_amount += (item.price * item.quantity)

            else:
                item.quantity = 0  # Can't buy if no stock left!
                messages.append('No stock left of the item ' + item.item + ' at current time.')
                cart_items.remove(item)
                db.session.delete(item)
                db.session.commit()

    return render_template('cart.html', user=user, cart_items=cart_items, total_amount=total_amount, messages=messages)


# Place order for items in cart
@app.route('/place_order/<int:user_id>', methods=['GET', 'POST'])
def place_order(user_id):
    messages = []
    total_amount = 0

    user = User.query.filter_by(id=user_id).first()
    cart_items = Cart.query.filter_by(added_by=user_id).all()

    for item in cart_items:
        product = Product.query.filter_by(name=item.item).first()

        if product.stock >= item.quantity:  # Another check before placing order
            product.stock -= item.quantity
            total_amount += (item.price * item.quantity)

        elif product.stock > 0:
            item.quantity = product.stock  # Can't buy more than is available!
            product.stock = 0
            messages.append(
                'Purchase of only ' + str(item.quantity) + ' of the item ' + item.item + ' was possible. No more stock '
                                                                                         'left by time of ordering. ')
            total_amount += (item.price * item.quantity)

        else:
            messages.append('No stock left of the item ' + item.item + ' by time of ordering.')
            cart_items.remove(item)

    # Putting them all together in a string (names and quantities)
    ordered_items = ', '.join([item.item + ' (' + str(item.quantity) + ')' for item in cart_items])

    order = Order(user_id=user_id, items=ordered_items, amount_paid=total_amount)
    db.session.add(order)
    db.session.commit()

    # Order placed, remove from cart
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    return render_template('order_placed.html', user=user, messages=messages)


# User's past orders
@app.route('/user_orders/<int:user_id>')
def user_orders(user_id):
    user = User.query.filter_by(id=user_id).first()
    orders = Order.query.filter_by(user_id=user_id).all()

    return render_template('user_orders.html', user=user, orders=orders)


# Displays all products available
@app.route('/view_products')
def view_products():
    products = Product.query.all()

    return render_template('view_products.html', products=products)


# Displays all categories
@app.route('/view_categories')
def view_categories():
    categories = Category.query.all()
    counts = [0] * len(categories)

    for i in range(len(categories)):
        category_name = categories[i].name
        category_products = Product.query.filter_by(category=category_name).all()
        counts[i] = len(category_products)

    return render_template('view_categories.html', categories=categories, counts=counts)


# Allows admin to add a product to the database
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    errors = []
    product_added = False

    if request.method == 'POST':
        name = request.form.get('name')
        image = request.form.get('image')
        category = request.form.get('category')
        price = request.form.get('price')
        stock = request.form.get('stock')
        best_before = request.form.get('best_before')

        # Input validation
        if not all(char.isalnum() or char.isspace() for char in name):
            errors.append('Names can only contain letters, numbers or spaces.')

        existing_product = Product.query.filter_by(name=name).first()
        if existing_product:
            errors.append('A product of that name already exists.')

        category = Category.query.filter_by(name=category).first()
        if not category:
            errors.append('That category does not exist.')

        price = float(price)
        if price <= 0:
            errors.append('Price cannot be less than or equal to zero.')

        stock = int(stock)
        if stock <= 0:
            errors.append('Stock cannot be less than or equal to zero.')

        units = ['day', 'days', 'week', 'weeks', 'month', 'months']
        best_before_parts = best_before.strip().split()
        if len(best_before_parts) != 2 or not best_before_parts[0].isdigit() or best_before_parts[1] not in units:
            errors.append('Best-before should contain a number, followed by any one of [day(s), week(s), month(s)].')

        if len(errors) == 0:
            new_product = Product(name=name, image=image, category=category.name, price=price, stock=stock,
                                  best_before=best_before)
            db.session.add(new_product)
            db.session.commit()
            product_added = True

    categories = Category.query.all()

    return render_template('add_product.html', categories=categories, errors=errors, product_added=product_added)


# Allows admin to modify details of a product
@app.route('/modify_product', methods=['GET', 'POST'])
def modify_product():
    errors = []
    product = None
    product_modified = False

    if request.method == 'POST':

        if 'current_name' in request.form:
            current_name = request.form.get('current_name')
            product = Product.query.filter_by(name=current_name).first()  # For displaying product info before modifying
            if not product:
                errors.append('No product of that name was found.')

        else:
            product_id = request.form.get('product_id')
            product = Product.query.filter_by(id=product_id).first()

            new_name = request.form.get('new_name')
            image = request.form.get('image')
            category = request.form.get('category')
            price = request.form.get('price')
            stock = request.form.get('stock')
            best_before = request.form.get('best_before')

            # Input validation (if there is input)
            if new_name != '':
                if not all(char.isalnum() or char.isspace() for char in new_name):
                    errors.append('Names can only contain letters, numbers or spaces.')

            if image != '':
                if not image.endswith(('.png', '.jpg', '.jpeg')):
                    errors.append('Image files can only be of the formats .png, .jpg or .jpeg')

            if category != '':
                category = Category.query.filter_by(name=category).first()
                if not category:
                    errors.append('That category does not exist.')

            if price != '':
                price = float(price)
                if price <= 0:
                    errors.append('Price cannot be less than or equal to zero.')

            if stock != '':
                stock = int(stock)
                if stock <= 0:
                    errors.append('Stock cannot be less than or equal to zero.')

            if best_before != '':
                units = ['day', 'days', 'week', 'weeks', 'month', 'months']
                best_before_parts = best_before.strip().split()
                if len(best_before_parts) != 2 or not best_before_parts[0].isdigit() or best_before_parts[1] \
                        not in units:
                    errors.append(
                        'Best-before should contain a number, followed by any one of [day(s), week(s), month(s)].')

            # Make requested changes
            if len(errors) == 0:
                if new_name != '':
                    product.name = new_name

                if image != '':
                    product.image = image

                if category != '':
                    product.category = category.name

                if price != '':
                    product.price = price

                if stock != '':
                    product.stock = stock

                if best_before != '':
                    product.best_before = best_before

                db.session.commit()
                product_modified = True

    categories = Category.query.all()

    return render_template('modify_product.html', categories=categories, product=product, errors=errors,
                           product_modified=product_modified)


# Allows admin to add a category to the database
@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    error = None
    category_added = False

    if request.method == 'POST':
        name = request.form.get('name')

        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            error = 'That category already exists.'  # Can't add something that's already there

        elif not all(char.isalpha() or char.isspace() for char in name):
            error = 'Category names can only have letters of the alphabet and spaces.'  # Single validation rule

        else:
            new_category = Category(name=name)
            db.session.add(new_category)
            db.session.commit()
            category_added = True

    return render_template('add_category.html', error=error, category_added=category_added)


# Allows admin to modify details of a category
@app.route('/modify_category', methods=['GET', 'POST'])
def modify_category():
    error = None
    category = None
    category_modified = False

    if request.method == 'POST':

        if 'current_name' in request.form:
            current_name = request.form.get('current_name')
            category = Category.query.filter_by(name=current_name).first()  # For displaying category info before modifying
            if not category:
                error = 'No category of that name was found.'

        else:
            category_id = request.form.get('category_id')
            category = Category.query.filter_by(id=category_id).first()

            new_name = request.form.get('new_name')

            # Input validation (if there is input)
            if new_name != '':
                if not all(char.isalpha() or char.isspace() for char in new_name):
                    error = 'Names can only contain letters, numbers or spaces.'

            # Make requested changes
            if error is None:
                if new_name != '':
                    category.name = new_name

                db.session.commit()
                category_modified = True

    return render_template('modify_category.html', category=category, error=error, category_modified=category_modified)


# Allows admin to remove a product from the database
@app.route('/delete_product', methods=['GET', 'POST'])
def delete_product():
    error = None
    product = None
    product_deleted = False

    if request.method == 'POST':

        if 'product_name' in request.form:
            product_name = request.form.get('product_name')

            product = Product.query.filter_by(name=product_name).first()
            if not product:
                error = 'No such product was found.'  # Can't remove something that isn't there

        elif 'product_id' in request.form:
            product_id = request.form.get('product_id')

            product = Product.query.filter_by(id=product_id).first()
            db.session.delete(product)
            db.session.commit()
            product_deleted = True

    return render_template('delete_product.html', product=product, product_deleted=product_deleted, error=error)


# Allows admin to remove a category from the database
@app.route('/delete_category', methods=['GET', 'POST'])
def delete_category():
    prod_count = None
    error = None
    category = None
    category_deleted = False

    if request.method == 'POST':

        if 'category_name' in request.form:
            category_name = request.form.get('category_name')

            category = Category.query.filter_by(name=category_name).first()
            if not category:
                error = 'No such category was found.'

            else:
                category_products = Product.query.filter_by(category=category_name).all()
                prod_count = len(category_products)  # No. of products in category

        elif 'category_name_conf' in request.form:
            category_name = request.form.get('category_name_conf')

            category_products = Product.query.filter_by(category=category_name).all()
            for product in category_products:
                db.session.delete(product)

            category_del = Category.query.filter_by(name=category_name).first()
            db.session.delete(category_del)
            db.session.commit()
            category_deleted = True

    return render_template('delete_category.html', category=category, category_deleted=category_deleted,
                           prod_count=prod_count, error=error)


app.run(debug=True)
