from flask import current_app
from flask_sse import ServerSentEventsBlueprint
from redis import StrictRedis


class CustomServerSentEventsBlueprint(ServerSentEventsBlueprint):
    @property
    def redis(self):
        redis_url = current_app.config.get("SSE_REDIS_URL")
        if not redis_url:
            redis_url = current_app.config.get("REDIS_URL")
        if not redis_url:
            raise KeyError("Must set a redis connection URL in app config.")
        return StrictRedis.from_url(redis_url, socket_timeout=None, retry_on_timeout=True)


sse = CustomServerSentEventsBlueprint('sse', __name__)
sse.add_url_rule(rule="", endpoint="stream", view_func=sse.stream)
