from fastapi import APIRouter, Response
from twilio.twiml.voice_response import VoiceResponse

router = APIRouter(tags=["voice"])


@router.post("/voice")
def voice():
    response = VoiceResponse()
    response.say(
        "Hello! Thank you for calling. This is the default response.",
        voice="alice",
    )
    return Response(content=str(response), media_type="application/xml")