from sqlalchemy import Column, Integer, Float, Text, ForeignKey
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Text, primary_key=True)
    name = Column(Text)
    email = Column(Text)
    gender = Column(Text)
    city = Column(Text)
    signup_date = Column(Text)


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Text, primary_key=True)
    product_name = Column(Text)
    category = Column(Text)
    brand = Column(Text)
    price = Column(Float)
    rating = Column(Float)


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Text, primary_key=True)
    user_id = Column(Text, ForeignKey("users.user_id"))
    order_date = Column(Text)
    order_status = Column(Text)
    total_amount = Column(Float)


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(Text, primary_key=True)
    order_id = Column(Text, ForeignKey("orders.order_id"))
    product_id = Column(Text, ForeignKey("products.product_id"))
    user_id = Column(Text, ForeignKey("users.user_id"))
    quantity = Column(Integer)
    item_price = Column(Float)
    item_total = Column(Float)


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Text, primary_key=True)
    order_id = Column(Text, ForeignKey("orders.order_id"))
    product_id = Column(Text, ForeignKey("products.product_id"))
    user_id = Column(Text, ForeignKey("users.user_id"))
    rating = Column(Integer)
    review_text = Column(Text)
    review_date = Column(Text)