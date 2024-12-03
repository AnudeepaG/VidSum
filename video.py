import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from googletrans import Translator, LANGUAGES

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define the improved summarization prompt
prompt = """You are an advanced YouTube video summarizer. Your task is to summarize the entire transcript provided, ensuring that the summary is clear, concise, and highly informative.

Please adhere to the following guidelines while summarizing the text:

1. **Bullet Points**: Present the summary in bullet points for easy reading and quick reference.
2. **Key Themes & Topics**: Identify and elaborate on the main themes, topics, or subjects discussed in the video. Ensure to highlight any major shifts in topic or important discussions.
3. **Actionable Insights & Takeaways**: Highlight any actionable advice, recommendations, or insights that the video offers to its viewers.
4. **Time Stamps**: Include time stamps (e.g., 01:25) when discussing key points or themes, so viewers can navigate directly to relevant sections.
5. **Sentiment Analysis**: Provide a brief sentiment analysis, highlighting the tone of the video (e.g., motivating, informative, reflective).
6. **Key Keywords**: List important keywords or phrases that are central to understanding the video’s content.
7. **Length**: The summary should be clear, concise, and not exceed 300 words. Prioritize clarity, relevance, and coherence.

Here is the transcript text for summarization: """

# Extract transcript details from YouTube
def extract_transcript_details(youtube_video_url, language='en'):
    try:
        video_id = youtube_video_url.split("=")[1]
        
        # Attempt to fetch transcript in the selected language
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        
    except NoTranscriptFound:
        # If no transcript available in selected language, attempt to fetch and translate the transcript to English
        st.warning(f"Transcript not available in {LANGUAGES.get(language, language)}. Attempting to retrieve a transcript and translate it to English.")
        try:
            # Fetch transcript in first available language
            transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Initialize translator for translating to English
            translator = Translator()
            translated_segments = []
            for segment in transcript_text:
                try:
                    translated_text = translator.translate(segment['text'], src=language, dest='en').text
                    translated_segments.append(translated_text)
                except AttributeError:
                    # Log segment if translation failed
                    st.error(f"Translation error for segment: {segment['text']} - Segment skipped due to an unexpected translation issue.")
                    continue
                except Exception as translation_error:
                    st.error(f"Unexpected error during translation: {translation_error}")
                    return None

            # Combine translated segments into a single string
            transcript_text = ' '.join(translated_segments)
        
        except NoTranscriptFound:
            st.error(f"No transcript available in {LANGUAGES.get(language, language)}.")
            return None
        except Exception as e:
            st.error(f"An error occurred during translation: {e}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

    # Combine transcript segments into a single string if in list format
    if isinstance(transcript_text, list):
        transcript = ' '.join([segment['text'] for segment in transcript_text])
    else:
        transcript = transcript_text

    return transcript

# Generate summary using Gemini model
def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt + transcript_text)
    return response.text

# Streamlit Interface with Modern UI
st.set_page_config(page_title="VidSums: Your YouTube Summarizer", layout="wide", page_icon="🎬")

# App Title and Tagline
st.title("🎬 VidSums: Your YouTube Summarizer")
st.markdown("### Turn those hours of YouTube into minutes of insights without the grind!🚀")

# Language selection dropdown with cleaner design
language_choice = st.selectbox(
    "🌍 **Pick your Transcript Language:**",
    options=list(LANGUAGES.keys()),  # Use language codes directly
    format_func=lambda lang: LANGUAGES[lang],
    help="Choose the language of the YouTube video's transcript."
)

# Create a clean input box for YouTube link
youtube_link = st.text_input(
    "🔗 **Paste Your YouTube Link Here**", 
    placeholder="https://www.youtube.com/watch?v=example", 
    label_visibility="collapsed"
)

if youtube_link:
    video_id = youtube_link.split("=")[1]
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

# Add fresh and fun custom styles to the app interface
st.markdown("""
    <style>
        body {
            background-color: #fafafa;
            font-family: 'Roboto', sans-serif;
        }
        .stButton button {
            background-color: #8e44ad;
            color: white;
            border-radius: 50px;
            padding: 16px 40px;
            font-size: 18px;
            font-weight: bold;
            box-shadow: 0px 4px 8px rgba(0,0,0,0.15);
            transition: background-color 0.3s ease, transform 0.2s ease;
        }
        .stButton button:hover {
            background-color: #9b59b6;
            transform: scale(1.05);
            box-shadow: 0px 6px 16px rgba(0,0,0,0.2);
        }
        .stTextInput input {
            border-radius: 12px;
            border: 2px solid #8e44ad;
            padding: 14px;
            font-size: 16px;
            color: #555;
        }
        .stTextInput input:focus {
            border-color: #9b59b6;
            box-shadow: 0 0 5px rgba(128, 0, 128, 0.5);
        }
        .stSelectbox select {
            border-radius: 12px;
            padding: 14px;
            background-color: #fff;
            border: 2px solid #8e44ad;
            font-size: 16px;
            color: #555;
        }
        .stSelectbox select:focus {
            border-color: #9b59b6;
            box-shadow: 0 0 5px rgba(128, 0, 128, 0.5);
        }
        .stText {
            color: #333;
            line-height: 1.5;
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

# Main action button
if st.button("🚀 **Transform My Video!**"):
    if youtube_link:
        transcript_text = extract_transcript_details(youtube_link, language_choice)
        if transcript_text:
            summary = generate_gemini_content(transcript_text, prompt)
            st.markdown("## 📝 **Your Quickfire Video Summary**")
            st.write(summary)
        else:
            st.warning("Oops, we couldn't retrieve the transcript. Try another video!")
    else:
        st.warning("😅 Please enter a valid YouTube link. We got you, fam!")
