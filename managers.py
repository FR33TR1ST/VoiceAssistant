import re
import subprocess
import platform


if platform.system() == "Windows":
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    def get_default_audio_endpoint():
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))


class InputManager:
    def __init__(self):
        self.commands = {
            "open": "start",
            "start": "start",
            "play": "media",
            "watch": "media",
            "youtube": "media",
            "set": "reminder",
            "search": "internet",
            "browser": "internet",
            "going": "maps",
            "time": "time",
            "day": "time",
            "translate": "translate",
            "stock": "stock",
            "joke": "joke",
            "volume": "volume",
        }
        self.stop_words = {"i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
                           "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers",
                           "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
                           "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
                           "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
                           "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
                           "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
                           "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
                           "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
                           "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
                           "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
                           "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"}

    def tokenize(self, input_text):
        # A simple tokenizer splitting by whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', input_text.lower())
        return tokens

    def classify_and_extract(self, input_text):
        tokens = self.tokenize(input_text)

        # Classification based on verbs known in the commands
        category = next((self.commands[token] for token in tokens if token in self.commands), "unknown")

        # Keyword Extraction
        keywords = []
        if category == "maps":
            for i, token in enumerate(tokens):
                if token not in self.stop_words:
                    # Append the street name
                    keywords.append(token)
                    # If the next token is a digit (street number), append it as well
                    if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                        keywords.append(tokens[i + 1])
                        break  # Break to prevent re-adding the number
        else:
            # Exclude stop words and digits, assuming keywords are significant words
            keywords = [token for token in tokens if token not in self.stop_words and not token.isdigit()]

        return category, keywords



class VolumeManager:
    def __init__(self, OS):
        self.OS = OS



    def increase(self, volume_percent, OS):
        if OS == "Windows":
            get_default_audio_endpoint().SetMasterVolumeLevelScalar(min(1.0, get_default_audio_endpoint().GetMasterVolumeLevelScalar() + volume_percent / 100), None)

        elif OS == "Linux":
            subprocess.run(f"pactl set-sink-volume @DEFAULT_SINK@ +{volume_percent}%", shell=True)
        elif OS == "Darwin":
            subprocess.run(f"osascript -e 'set volume output volume (output volume of (get volume settings) + {volume_percent})'", shell=True)
        return f'Volume increased by {volume_percent}%'

    def decrease(self, volume_percent, OS):
        if OS == "Windows":
            get_default_audio_endpoint().SetMasterVolumeLevelScalar(min(0.0, get_default_audio_endpoint().GetMasterVolumeLevelScalar() - volume_percent / 100), None)
        elif OS == "Linux":
            subprocess.run(f"pactl set-sink-volume @DEFAULT_SINK@ -{volume_percent}%", shell=True)
        elif OS == "Darwin":
            subprocess.run(f"osascript -e 'set volume output volume (output volume of (get volume settings) - {volume_percent})'", shell=True)
        return f'Volume decreased by {volume_percent}%'

    def mute(self, OS):
        if OS == "Windows":
            if get_default_audio_endpoint().GetMute() == 0:
                get_default_audio_endpoint().SetMute(1, None)
            else:
                get_default_audio_endpoint().SetMute(0, None)
        elif OS == "Linux":
            subprocess.run("pactl set-sink-mute @DEFAULT_SINK@ toggle", shell=True)
        elif OS == "Darwin":
            subprocess.run("osascript -e 'set volume output muted true'", shell=True)

    def max(self, OS):
        if OS == "Windows":
            get_default_audio_endpoint().SetMasterVolumeLevelScalar(1.0, None)
        elif OS == "Linux":
            subprocess.run("pactl set-sink-volume @DEFAULT_SINK@ 100%", shell=True)
        elif OS == "Darwin":
            subprocess.run("osascript -e 'set volume output volume 100'", shell=True)
        return 'Volume at the maximum'

    def is_muted(self, OS):
        if OS == "Windows":
            return 1 == get_default_audio_endpoint().GetMute()
        elif OS == "Linux":
            return 'yes' in subprocess.check_output("pactl get-sink-mute @DEFAULT_SINK@",
                                                    shell=True).decode('utf-8').strip()
        elif OS == "Darwin":
            return 'yes' in subprocess.check_output("osascript -e 'output muted of (get volume settings)'",
                                                    shell=True).decode('utf-8').strip()

    def __str__(self, OS):
        if OS == "Windows":
            interface = AudioUtilities.GetSpeakers().Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return int(cast(interface, POINTER(IAudioEndpointVolume)).GetMasterVolumeLevelScalar() * 100)
        elif OS == "Linux":
            if 'yes' in subprocess.check_output("pactl get-sink-mute @DEFAULT_SINK@", shell=True).decode('utf-8').strip():
                return 'Muted'
            else:
                return subprocess.check_output("pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\\d+%' | head -1",
                                               shell=True).decode('utf-8').rstrip('%').strip().rstrip('%') + '%'
        elif OS == "Darwin":
            return subprocess.check_output("osascript -e 'output volume of (get volume settings)'",
                                           shell=True).decode('utf-8').strip().rstrip('%') + '%'
