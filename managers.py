import re
import subprocess
import platform
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
import torch
import spacy
import os


if platform.system() == "Windows":
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    def get_default_audio_endpoint():
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))


class NLU_Dataset(torch.utils.data.Dataset):
    #A PyTorch Dataset class to store tokenized data and labels.
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item


class InputManager:
    #A class for managing input extraction, tokenization, and intent classification.
    def __init__(self, dataset_path='Dataset.csv'):
        #Initializes the InputManager with a model, tokenizer, and dataset.
        self.nlp = spacy.load('en_core_web_trf')

        # Define action words without duplicates
        self.action_words = {'play', 'open', 'book', 'set', 'turn', 'call', 'email', 'buy', 'cook', 'send', 'increase',
                             'decrease', 'mute', 'lock', 'unlock', 'remind', 'wake', 'schedule', 'watch', 'read',
                             'write', 'summarize', 'submit', 'practice', 'message', 'update', 'listen', 'find',
                             'search', 'get', 'make', 'give', 'take', 'tell', 'ask', 'work', 'go', 'do', 'be', 'have',
                             'prepare', 'pack', 'check', 'respond', 'delete', 'start', 'stop', 'pause', 'resume',
                             'drive', 'park', 'notify', 'forget', 'order', 'share', 'light', 'close', 'strike',
                             'continue', 'begin', 'finish', 'analyze', 'proceed', 'monitor', 'log', 'facilitate',
                             'engage', 'optimize', 'deploy', 'research', 'compile', 'pick', 'drop', 'wrap', 'meet',
                             'discuss', 'inform', 'shut', 'put', 'connect', 'disconnect', 'install', 'uninstall',
                             'activate', 'deactivate', 'adjust', 'clear', 'show', 'hide', 'track', 'follow', 'block',
                             'unblock', 'build', 'fix', 'draw', 'print', 'edit', 'clip', 'crop', 'zoom', 'upload',
                             'download', 'record', 'stream', 'playback', 'charge', 'pay', 'deliver', 'explore',
                             'design', 'test', 'help', 'assist', 'update', 'organize', 'remind', 'plan', 'recommend',
                             'subscribe', 'unsubscribe', 'post', 'comment', 'like', 'dislike', 'tag', 'mention', 'call',
                             'text', 'scan', 'encrypt', 'decrypt', 'sign', 'authenticate', 'scan', 'record', 'repeat',
                             'shuffle', 'translate', 'tell'}

        # Initialize tokenizer and model
        self.tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')

        # Load the dataset
        self._load_dataset(dataset_path)

        # Initialize tokenizer and model
        self.tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
        self._prepare_model()

    def _load_dataset(self, dataset_path):
        #Loads the dataset and splits it into training and testing sets.
        try:
            dataset = pd.read_csv(dataset_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Dataset not found at {dataset_path}: {e}")

        X_train, X_test, y_train, y_test = train_test_split(
            dataset['Sentence'], dataset['Intent'], test_size=0.2, random_state=42
        )

        self.intent_labels = dataset['Intent'].unique()
        self.intent_label_map = {label: idx for idx, label in enumerate(self.intent_labels)}

        # Encode and create datasets
        self.train_dataset = self._create_dataset(X_train, y_train)
        self.test_dataset = self._create_dataset(X_test, y_test)

    def _create_dataset(self, sentences, labels):
        #Encodes sentences and maps labels to integers.
        encodings = self.tokenizer(list(sentences), truncation=True, padding=True, max_length=128)
        mapped_labels = [self.intent_label_map[label] for label in labels]
        return NLU_Dataset(encodings, torch.tensor(mapped_labels))

    def _prepare_model(self):
        # Define the model path
        model_path = './distilbert_model.pth'
        
        # Initialize the model
        model = DistilBertForSequenceClassification.from_pretrained(
            'distilbert-base-uncased', num_labels=len(self.intent_labels)
        )

        # Check if the model file exists
        if os.path.exists(model_path):
            # Load the saved model
            model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            model.eval()
            print("Model loaded from disk.")
        else:
            # Set up training arguments and train the model
            training_args = TrainingArguments(
                output_dir='./results', num_train_epochs=3, per_device_train_batch_size=16,
                per_device_eval_batch_size=64, warmup_steps=500, weight_decay=0.01,
                logging_dir='./logs', logging_steps=10, evaluation_strategy="steps"
            )

            self.trainer = Trainer(
                model=model, args=training_args, train_dataset=self.train_dataset,
                eval_dataset=self.test_dataset
            )
            self.trainer.train()

            # Save the trained model
            torch.save(model.state_dict(), model_path)
            print("Model trained and saved to disk.")
        
        # Assign the trainer to the instance for further use
        self.trainer = Trainer(model=model)

    def extract_intentions(self, sentence):
        #Extracts intentions from a given sentence.
        if not sentence:
            return []

        doc = self.nlp(sentence)
        intentions, current_intent = [], []

        for token in doc:
            is_action = token.lemma_.lower() in self.action_words and token.pos_ in ('VERB', 'AUX')

            if is_action and current_intent:
                intentions.append(' '.join(tok.text for tok in current_intent).strip())
                current_intent = []

            current_intent.append(token)

            if token.dep_ == 'cc' and current_intent:
                intentions.append(' '.join(tok.text for tok in current_intent).strip())
                current_intent = []

        if current_intent:
            intentions.append(' '.join(tok.text for tok in current_intent).strip())

        return intentions

    def split_and_categorize(self, user_input):
        # Splits and categorizes the user input into intents.
        sentences_predict = self.extract_intentions(user_input)
        df_sentences = pd.DataFrame(sentences_predict, columns=['sentences'])

        # Check if there are any sentences to process
        if df_sentences.empty or df_sentences['sentences'].str.strip().eq('').all():
            print("No valid sentences to categorize.")
            return pd.DataFrame(columns=['sentences', 'Predicted Intent'])

        # Ensure the trainer is initialized
        if not hasattr(self, 'trainer') or self.trainer is None:
            try:
                print("Trainer not initialized. Attempting to prepare the model...")
                self._prepare_model()
            except Exception as e:
                print("Error initializing the model and trainer:", e)
                return pd.DataFrame(columns=['sentences', 'Predicted Intent'])

        # Proceed with predictions if trainer is successfully initialized
        try:
            encodings = self.tokenizer(list(df_sentences['sentences']), truncation=True, padding=True, max_length=128)
            new_dataset = NLU_Dataset(encodings, torch.tensor([0] * len(df_sentences)))

            predictions = self.trainer.predict(new_dataset)
            new_preds = torch.tensor(predictions.predictions).argmax(axis=-1)

            df_sentences['Predicted Intent'] = [self.intent_labels[pred] for pred in new_preds]
            return df_sentences

        except Exception as e:
            print("An error occurred during prediction:", e)
            return pd.DataFrame(columns=['sentences', 'Predicted Intent'])


class VolumeManager:
    def __init__(self, OS):
        self.OS = OS

    def set_volume(self, volume_percent, OS):
        if OS == "Windows":
            get_default_audio_endpoint().SetMasterVolumeLevelScalar(min(1.0, volume_percent / 100), None)
        elif OS == "Linux":
            subprocess.run(f"pactl set-sink-volume @DEFAULT_SINK@ {volume_percent}%", shell=True)
        elif OS == "Darwin":
            subprocess.run(f"osascript -e 'set volume output volume {volume_percent}'", shell=True)
        return f'Volume set to {volume_percent}%'


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
