from app import db
from hashlib import md5


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    # User’ 是这种关系中的右边的表(实体)(左边的表/实体是父类)。因为定义一个自我指向的关系，我们在两边使用同样的类。
    followed = db.relationship('User',
        # secondary 指明了用于这种关系的辅助表。
        secondary=followers,
        # primaryjoin 表示辅助表中连接左边实体(发起关注的用户)的条件。注意因为 followers 表不是一个模式，获得字段名的语法有些怪异。
        primaryjoin=(followers.c.follower_id == id),
        # secondaryjoin 表示辅助表中连接右边实体(被关注的用户)的条件。
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

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

    def avatar(self, size):
        # vatar 返回用户图片的 URL，以像素为单位缩放成要求的尺寸
        return 'http://www.gravatar.com/avatar/' + md5(self.email.encode('utf8')).hexdigest() + '?d=mm&s=' + str(size)

    @staticmethod
    def make_unique_nickname(nickname):
        if not User.query.filter_by(nickname=nickname).first():
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if not User.query.filter_by(nickname=new_nickname).first():
                break
            version += 1
        return new_nickname

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def followed_posts(self):
        return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc())


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % self.body
