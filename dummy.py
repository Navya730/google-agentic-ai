
import mimetypes

# ADK imports
import adk
from adk import Agent, AgentTool
from adk.tools import get_agriculture_data, get_current_time

# Assuming you have these agents/tools defined elsewhere
# from your_agents import crop_recommendation, update_personal_information, news_analyst

app = Flask(__name__)
CORS(app)

# Your existing agent configuration with audio support
root_agent = Agent(
    name="farmer_assistant",
    model="gemini-2.0-flash-exp",
    description="Farmer Assistant with Audio Support",
    instruction="""
    You are a farmer assistant that helps farmers with their queries through both text and audio input.
    You can understand spoken questions and provide helpful responses.

    Handle these types of queries using the appropriate tool/agent:

    For queries related to crop recommendation use the agent:
    crop_recommendation

    Every time you get personal information use the agent:
    update_personal_information

    For Mandi price information for a given state use the tool. If the tool doesn't respond use the news_analyst tool:
    get_agriculture_data

    For news-related questions or current time queries use:
    news_analyst or get_current_time

    When processing audio:
    - Listen carefully to the farmer's spoken question
    - Understand their farming context and needs
    - Provide clear, helpful responses
    - If audio is unclear, politely ask them to repeat
    """,
    # sub_agents=[crop_recommendation, update_personal_information],  # Uncomment when you have these
    tools=[
        # AgentTool(news_analyst),  # Uncomment when you have this
        get_agriculture_data,
        get_current_time,
        adk.tools.preload_memory_tool.PreloadMemoryTool()
    ],
)


class AudioEnabledFarmerAgent:
    def __init__(self, agent: Agent):
        self.agent = agent

    async def process_audio_input(self, audio_data: bytes, mime_type: str = "audio/webm"):
        """Process audio input directly with the ADK agent"""
        try:
            # Create the audio input for Gemini 2.0 Flash
            # The model will handle audio natively without transcription
            audio_input = {
                "mime_type": mime_type,
                "data": audio_data
            }

            # Use the agent's model to process audio directly
            response = await self.agent.run_async([
                "Listen to this audio message from a farmer and help them with their query.",
                audio_input
            ])

            return response

        except Exception as e:
            print(f"Error processing audio: {e}")
            return f"I'm sorry, I had trouble understanding your audio message. Could you please try again? Error: {str(e)}"

    async def process_text_input(self, text: str):
        """Process text input with the ADK agent"""
        try:
            response = await self.agent.run_async(text)
            return response

        except Exception as e:
            print(f"Error processing text: {e}")
            return f"I encountered an error processing your message: {str(e)}"


# Initialize the audio-enabled farmer agent
audio_farmer_agent = AudioEnabledFarmerAgent(root_agent)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "ADK Farmer Assistant with Audio Support is running",
        "agent": "farmer_assistant",
        "model": "gemini-2.0-flash-exp",
        "capabilities": ["text", "audio", "crop_recommendation", "mandi_prices", "news"]
    })


@app.route('/chat/audio', methods=['POST'])
async def process_audio():
    """Process audio input from farmers"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']
        audio_data = audio_file.read()

        # Determine MIME type
        filename = audio_file.filename or 'audio.webm'
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type or not mime_type.startswith('audio/'):
            mime_type = "audio/webm"

        print(f"Processing farmer audio query - MIME type: {mime_type}")

        # Process with the audio-enabled agent
        response = await audio_farmer_agent.process_audio_input(audio_data, mime_type)

        return jsonify({
            "response": response,
            "input_type": "audio",
            "mime_type": mime_type,
            "agent": "farmer_assistant",
            "status": "success"
        })

    except Exception as e:
        print(f"Error in audio processing: {e}")
        return jsonify({
            "error": f"Failed to process audio: {str(e)}",
            "status": "error"
        }), 500


@app.route('/chat/text', methods=['POST'])
async def process_text():
    """Process text input from farmers"""
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400

        message = data['message']
        print(f"Processing farmer text query: {message}")

        # Process with the ADK agent
        response = await audio_farmer_agent.process_text_input(message)

        return jsonify({
            "input_message": message,
            "response": response,
            "input_type": "text",
            "agent": "farmer_assistant",
            "status": "success"
        })

    except Exception as e:
        print(f"Error in text processing: {e}")
        return jsonify({
            "error": f"Failed to process text: {str(e)}",
            "status": "error"
        }), 500


@app.route('/chat', methods=['POST'])
async def unified_chat():
    """Unified endpoint that handles both audio and text input"""
    try:
        # Check input type
        if 'audio' in request.files:
            # Route to audio processing
            return await process_audio()
        elif request.is_json:
            # Route to text processing
            return await process_text()
        else:
            return jsonify({
                "error": "Invalid input format. Send either audio file or JSON with 'message' field",
                "status": "error"
            }), 400

    except Exception as e:
        return jsonify({
            "error": f"Chat processing failed: {str(e)}",
            "status": "error"
        }), 500


@app.route('/agent/info', methods=['GET'])
def agent_info():
    """Get information about the farmer assistant agent"""
    return jsonify({
        "name": root_agent.name,
        "model": root_agent.model,
        "description": root_agent.description,
        "capabilities": {
            "crop_recommendation": "Provides crop recommendations based on soil, weather, etc.",
            "personal_information": "Updates and manages farmer personal information",
            "mandi_prices": "Fetches current market prices for agricultural products",
            "news_analysis": "Provides agricultural news and updates",
            "audio_input": "Processes spoken queries from farmers",
            "text_input": "Processes written queries from farmers"
        },
        "supported_audio_formats": ["webm", "wav", "mp3", "ogg"],
        "status": "active"
    })


# Alternative direct ADK runner (without Flask)
async def run_agent_with_audio():
    """Direct ADK agent runner for audio input"""
    print("🚜 Starting ADK Farmer Assistant with Audio Support")
    print("📱 Listening for farmer queries...")

    # Example of running the agent directly
    while True:
        try:
            # In a real implementation, you'd get audio input from a microphone or file
            user_input = input("\n💬 Type your farming question (or 'quit' to exit): ")

            if user_input.lower() in ['quit', 'exit']:
                break

            # Process text input
            response = await audio_farmer_agent.process_text_input(user_input)
            print(f"🤖 Farmer Assistant: {response}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

    print("👋 Goodbye! Happy farming!")


if __name__ == '__main__':
    import sys

    print("🚜 ADK Farmer Assistant with Audio Support")
    print("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == 'direct':
        # Run agent directly
        asyncio.run(run_agent_with_audio())
    else:
        # Run Flask API server
        print("🌐 Starting API server...")
        print("📋 Available endpoints:")
        print("  - POST /chat/audio  - Process audio from farmers")
        print("  - POST /chat/text   - Process text from farmers")
        print("  - POST /chat        - Unified audio/text endpoint")
        print("  - GET  /health      - Health check")
        print("  - GET  /agent/info  - Agent information")
        print()
        print("🎤 Audio formats: WebM, WAV, MP3, OGG")
        print("🤖 Model: gemini-2.0-flash-exp")
        print()
        print("Run with 'python agent.py direct' for direct terminal interaction")
        print("=" * 50)

        app.run(host='0.0.0.0', port=5000, debug=True)