import redis
import pickle


class SimpleQueue:
    def __init__(self, conn: redis.Redis, name: str):
        if conn.exists(name):
            conn.delete(name)

        self.conn = conn
        self.name = name

    def put(self, item) -> None:
        serialized_item = pickle.dumps(item, protocol=pickle.HIGHEST_PROTOCOL)
        self.conn.lpush(self.name, serialized_item)

    def get(self):
        _, serialized_item = self.conn.brpop(self.name)
        return pickle.loads(serialized_item)

    def get_length(self) -> int:
        return self.conn.llen(self.name)

    def empty(self) -> bool:
        return not bool(self.get_length())

    def __len__(self):
        return self.get_length()
