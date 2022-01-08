
class Config(object):
    WTF_CSRF_ENABLED = True
    SECRET_KEY = 'HiS-tEnd3r-heIr-miGht-Bear-hiS-m3m0Ry'
    TEMPLATES_AUTO_RELOAD = True

    BASIC_AUTH_USERNAME='metrics'
    BASIC_AUTH_PASSWORD='nevernever'
    BASIC_AUTH_FORCE=True
    SESSION_TYPE = 'filesystem'
