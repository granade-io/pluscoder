from lxml import etree


class XMLStreamParser:
    def __init__(self):
        self.parser = etree.XMLPullParser(events=("start", "end"), recover=True)
        self.select_tags = ["pc_action", "pc_content", "pc_thinking"]
        self.subscribers = []

    def subscribe(self, callback):
        """Subscribe a callback function to handle tag end events"""
        self.subscribers.append(callback)

    def on_tag_end(self, element):
        """Notify all subscribers when a tag ends"""
        for subscriber in self.subscribers:
            subscriber(element)

    def process_parse_events(self):
        for action, element in self.parser.read_events():
            if element.tag not in self.select_tags:
                continue
            if action == "end":
                self.on_tag_end(element)

    def start_stream(self):
        self.parser = etree.XMLPullParser(events=("start", "end"), recover=True)

    def close_stream(self):
        self.parser.close()

    def stream(self, chunk: str):
        if isinstance(chunk, list) and len(chunk) >= 0:
            chunk = "".join([c["text"] for c in chunk if c["type"] == "text"])
        elif isinstance(chunk, str):
            pass
        else:
            error = "Not chunk type"
            raise ValueError(error)

        self.parser.feed(chunk)
        self.process_parse_events()
