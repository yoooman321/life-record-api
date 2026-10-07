from fastapi.responses import JSONResponse


class EnvelopeJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        envelope = {"status": "success", "data": content}
        return super().render(envelope)
