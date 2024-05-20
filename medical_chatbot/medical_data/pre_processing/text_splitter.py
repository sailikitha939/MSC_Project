class RecursiveTextSplitter:
    def __init__(self, max_chunk_size):
        self.max_chunk_size = max_chunk_size

    def split_text(self, text):
        return self._split_recursive(text, [])

    def _split_recursive(self, text, chunks):
        if len(text) <= self.max_chunk_size:
            chunks.append(text)
            return chunks
        else:
            # Find a suitable point to split
            split_point = self._find_split_point(text)
            # Split and recursively process each part
            return self._split_recursive(text[:split_point], chunks) + \
                   self._split_recursive(text[split_point:], chunks)

    def _find_split_point(self, text):
        return min(len(text), self.max_chunk_size)
