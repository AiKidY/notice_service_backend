
class PgOpError(Exception):
    def __init__(self, errorinfo):
        super(PgOpError, self).__init__(self) #初始化父类
        self.errorinfo=errorinfo
    def __str__(self):
        return self.errorinfo
