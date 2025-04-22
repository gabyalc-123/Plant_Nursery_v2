from . import db
from sqlalchemy import Sequence


class CareInstruction(db.Model):
    __bind_key__ = 'db'
    id = db.Column(db.Integer, Sequence('CareInstruction_sequence'), unique=True, nullable=False, primary_key=True)
    product_id = db.Column(db.Integer)
    instructions = db.Column(db.Text, nullable=False)
