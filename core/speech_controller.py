"""Owns playback cancellation without network requests or device restarts."""
class SpeechController:
    def __init__(self):
        self.output = None

    def bind(self, output):
        self.output = output

    def cancel(self, queue):
        if self.output is not None:
            self.output.discard_pending()
        if queue is not None:
            while not queue.empty():
                queue.get_nowait()

    def token(self):
        return self.output.generation if self.output is not None else None

    def write(self, data, token):
        if self.output is not None:
            self.output.write(data, generation=token)
