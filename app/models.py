from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(120), index=True, unique = True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    # 用户的对象是否允许被认证
    @property
    def is_authenticated(self):
        return True

    # 用户是否有效
    @property
    def is_active(self):
        return True

    # 是否允许匿名用户登录系统
    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            # python3
            return str(self.id)
        except NameError:
            # python2
            return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.nickname


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.Integer, db.ForeignKey(User.id))

    def __repr__(self):
        return '<Post %r>' % self.body
