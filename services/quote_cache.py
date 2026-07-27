import random

class QuoteCache:
    def __init__(self):
        self._quotes = []
        self.loaded = False

    @property
    def quotes(self):
        return self._quotes

    def add(self, message):
        if message.author.bot:
            return

        if message.content.strip() or message.attachments:
            self._quotes.append(message)

    def random(self):
        if not self._quotes:
            return None

        return random.choice(self._quotes)

    def clear(self):
        self._quotes.clear()

    def __len__(self):
        return len(self._quotes)
