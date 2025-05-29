import tkinter as tk
from tkinter import filedialog
import os
from PIL import Image, ImageTk
import tempfile
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TYER, ID3NoHeaderError, APIC
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.aac import AAC
from mutagen.wave import WAVE
import io
import glob
from mutagen.flac import Picture


class AudioTagEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Tag Editor")
        self.root.geometry("400x600")

        self.file_chosen = False
        self.file_path = ""
        self.file_name = ""
        self.verify_label = None
        self.temp_path = None
        self.file_type = None
        self.cover_art_label = None
        
        self.cover_art_selected = False

        self.label = tk.Label(root, text="Choose an audio file")
        self.label.grid(row=0, column=0)

        self.button = tk.Button(root, text="Open File", command=self.choose_file)
        self.button.grid(row=0, column=1)

        # Placeholders for tag entry widgets
        self.tag_widgets = {}

    def is_audio_file(self, file_path):
        return file_path.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a'))

    def choose_file(self):
        file_path = filedialog.askopenfilename(
            title="Select an Audio File",
            filetypes=(("Audio Files", "*.mp3 *.wav *.flac *.ogg *.aac *.m4a"),
                       ("All Files", "*.*"))
        )
        if file_path and self.is_audio_file(file_path):
            self.file_path = file_path
            self.file_name = os.path.basename(file_path)
            self.label.config(text=f"{self.file_name}", width=30)
            self.file_chosen = True
            self.file_type = os.path.splitext(self.file_name)[1].lower()
            if self.verify_label:
                self.verify_label.destroy()
            self.verify_label = tk.Label(self.root, text="File selected successfully!")
            self.verify_label.grid(row=1, column=0, columnspan=2)
            self.show_tag_options()
        else:
            self.label.config(text="Error: No audio file selected.")
            if self.verify_label:
                self.verify_label.destroy()
                self.verify_label = None
            self.hide_tag_options()

    def show_tag_options(self):
        # Remove previous widgets if any
        self.hide_tag_options()

        fields = ["Song Name", "Artist", "Album", "Genre", "Year"]
        self.tag_widgets = {}

        for idx, field in enumerate(fields, start=2):
            lbl = tk.Label(self.root, text=field + ":")
            lbl.grid(row=idx, column=0, sticky="e", padx=5, pady=2)
            entry = tk.Entry(self.root, width=20)
            entry.grid(row=idx, column=1, padx=5, pady=2)
            self.tag_widgets[field] = entry

        # Cover Art Button
        self.cover_art_button = tk.Button(self.root, text="Choose Cover Art", command=self.choose_cover_art)
        self.cover_art_button.grid(row=idx+1, column=0, columnspan=2, pady=10)
        self.cover_art_label = tk.Label(self.root, text="")
        self.cover_art_label.grid(row=idx+2, column=0, columnspan=2)

        # Save Button
        self.save_button = tk.Button(self.root, text="Save Tags", command=self.save_tags)
        self.save_button.grid(row=idx+3, column=0, columnspan=2, pady=10)

        # Now it's safe to grab existing tags
        self.grab_existing_tags()

    def grab_existing_tags(self):
        print("Grabbing existing tags...")
        if not self.file_chosen:
            print("No file chosen to grab tags from.")
            return

        try:
            if self.file_type == ".mp3":
                self._grab_mp3_tags()
            elif self.file_type == ".m4a" or self.file_type == ".mp4":
                self._grab_m4a_tags()
            elif self.file_type == ".flac":
                self._grab_flac_tags()
            elif self.file_type == ".ogg":
                self._grab_ogg_tags()
            elif self.file_type == ".aac":
                self._grab_aac_tags()
            elif self.file_type == ".wav":
                self._grab_wav_tags()
            else:
                print(f"Unsupported file type: {self.file_type}")
                return
        except Exception as e:
            print(f"Error loading tags: {e}")

    def _grab_mp3_tags(self):
        audio = MP3(self.file_path, ID3=ID3)
        print(f"Loaded MP3 tags for {self.file_name}")
        tag_map = {
            "TIT2": "Song Name",
            "TPE1": "Artist",
            "TALB": "Album",
            "TCON": "Genre",
            "TYER": "Year"
        }
        for tag in tag_map:
            if tag in audio.tags:
                tag_name = tag_map[tag]
                self.tag_widgets[tag_name].insert(0, audio.tags[tag].text[0])
                print(f"Existing tag {tag_name}: {audio.tags[tag].text[0]}")
        # Display existing cover art if present
        apic_key = next((k for k in audio.tags.keys() if k.startswith("APIC")), None)
        if apic_key:
            apic = audio.tags[apic_key]
            image_data = apic.data
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail((150, 150))
            self.cover_art_image = ImageTk.PhotoImage(image)
            self.cover_art_label.config(image=self.cover_art_image, text="")
            print("Displayed existing cover art.")
        else:
            self.cover_art_label.config(image="", text="No cover art found.")

    def _grab_m4a_tags(self):
        audio = MP4(self.file_path)
        print(f"Loaded MP4/M4A tags for {self.file_name}")
        tag_map = {
            "\xa9nam": "Song Name",
            "\xa9ART": "Artist",
            "\xa9alb": "Album",
            "\xa9gen": "Genre",
            "\xa9day": "Year"
        }
        for mp4_tag, field in tag_map.items():
            value = audio.tags.get(mp4_tag)
            if value and len(value) > 0:
                self.tag_widgets[field].insert(0, value[0])
                print(f"Existing tag {field}: {value[0]}")
        # Display cover art if present
        covr = audio.tags.get("covr")
        if covr and len(covr) > 0:
            image_data = covr[0]
            try:
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((150, 150))
                self.cover_art_image = ImageTk.PhotoImage(image)
                self.cover_art_label.config(image=self.cover_art_image, text="")
                print("Displayed existing cover art.")
            except Exception as e:
                print(f"Error displaying cover art: {e}")
                self.cover_art_label.config(image="", text="No cover art found.")
        else:
            self.cover_art_label.config(image="", text="No cover art found.")

    def _grab_flac_tags(self):
        audio = FLAC(self.file_path)
        print(f"Loaded FLAC tags for {self.file_name}")
        tag_map = {
            "TITLE": "Song Name",
            "ARTIST": "Artist",
            "ALBUM": "Album",
            "GENRE": "Genre",
            "DATE": "Year"
        }
        for flac_tag, field in tag_map.items():
            value = audio.get(flac_tag)
            if value and len(value) > 0:
                self.tag_widgets[field].insert(0, value[0])
                print(f"Existing tag {field}: {value[0]}")
        # Display cover art if present
        if audio.pictures:
            picture = audio.pictures[0]
            image_data = picture.data
            try:
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((150, 150))
                self.cover_art_image = ImageTk.PhotoImage(image)
                self.cover_art_label.config(image=self.cover_art_image, text="")
                print("Displayed existing cover art.")
            except Exception as e:
                print(f"Error displaying cover art: {e}")
                self.cover_art_label.config(image="", text="No cover art found.")
        else:
            self.cover_art_label.config(image="", text="No cover art found.")

    def _grab_ogg_tags(self):
        audio = OggVorbis(self.file_path)
        print(f"Loaded OGG tags for {self.file_name}")
        tag_map = {
            "TITLE": "Song Name",
            "ARTIST": "Artist",
            "ALBUM": "Album",
            "GENRE": "Genre",
            "DATE": "Year"
        }
        for ogg_tag, field in tag_map.items():
            value = audio.get(ogg_tag)
            if value and len(value) > 0:
                self.tag_widgets[field].insert(0, value[0])
                print(f"Existing tag {field}: {value[0]}")
        self.cover_art_label.config(image="", text="No cover art found.")

    def _grab_aac_tags(self):
        try:
            audio = AAC(self.file_path)
            print(f"Loaded AAC tags for {self.file_name}")
            # AAC files may use ID3 tags
            if hasattr(audio, 'tags') and audio.tags:
                tag_map = {
                    "TIT2": "Song Name",
                    "TPE1": "Artist",
                    "TALB": "Album",
                    "TCON": "Genre",
                    "TYER": "Year"
                }
                for tag in tag_map:
                    if tag in audio.tags:
                        tag_name = tag_map[tag]
                        self.tag_widgets[tag_name].insert(0, audio.tags[tag].text[0])
                        print(f"Existing tag {tag_name}: {audio.tags[tag].text[0]}")
        except Exception as e:
            print(f"Error loading AAC tags: {e}")
        self.cover_art_label.config(image="", text="No cover art found.")

    def _grab_wav_tags(self):
        try:
            audio = WAVE(self.file_path)
            print(f"Loaded WAV tags for {self.file_name}")
            # WAV files may use ID3 tags
            if hasattr(audio, 'tags') and audio.tags:
                tag_map = {
                    "TIT2": "Song Name",
                    "TPE1": "Artist",
                    "TALB": "Album",
                    "TCON": "Genre",
                    "TYER": "Year"
                }
                for tag in tag_map:
                    if tag in audio.tags:
                        tag_name = tag_map[tag]
                        self.tag_widgets[tag_name].insert(0, audio.tags[tag].text[0])
                        print(f"Existing tag {tag_name}: {audio.tags[tag].text[0]}")
        except Exception as e:
            print(f"Error loading WAV tags: {e}")
        self.cover_art_label.config(image="", text="No cover art found.")

    def save_tags(self):
        if self.file_type == ".mp3":
            self.save_mp3_tags()
        elif self.file_type == ".flac":
            self.save_flac_tags()
        elif self.file_type == ".ogg":
            self.save_ogg_tags()
        elif self.file_type == ".aac":
            self.save_aac_tags()
        elif self.file_type == ".m4a":
            self.save_m4a_tags()
        elif self.file_type == ".wav":
            self.save_wav_tags()
        else:
            print("Unsupported file type for saving tags.")

    def get_tag_values(self):
        """Return a dict of tag values from the entry widgets."""
        return {
            "Song Name": self.tag_widgets["Song Name"].get(),
            "Artist": self.tag_widgets["Artist"].get(),
            "Album": self.tag_widgets["Album"].get(),
            "Genre": self.tag_widgets["Genre"].get(),
            "Year": self.tag_widgets["Year"].get(),
        }

    def show_success_label(self, message="Tags saved successfully!"):
        if hasattr(self, 'success_label') and self.success_label:
            self.success_label.destroy()
        self.success_label = tk.Label(self.root, text=message, fg="green")
        self.success_label.grid(row=0, column=0, columnspan=2, pady=5)

    def cleanup_temp_cover(self):
        if self.temp_path:
            temp_dir = os.path.dirname(self.temp_path)
            for f in glob.glob(os.path.join(temp_dir, "ATE_*")):
                try:
                    os.remove(f)
                except Exception as e:
                    # Ignore errors about file being used by another process
                    if "used by another process" not in str(e):
                        print(f"Error removing temp file {f}: {e}")
            self.temp_path = None
            self.cover_art_selected = False

    def save_mp3_tags(self):
        try:
            audio = MP3(self.file_path, ID3=ID3)
            print(f"Loaded MP3 tags for {self.file_name}")
            
            # Ensure tags exist
            if audio.tags is None:
                audio.add_tags()
                
            tags = self.get_tag_values()
            # Remove and add tags
            for tag, frame, value in [
                ("TIT2", TIT2, tags["Song Name"]),
                ("TPE1", TPE1, tags["Artist"]),
                ("TALB", TALB, tags["Album"]),
                ("TCON", TCON, tags["Genre"]),
                ("TYER", TYER, tags["Year"]),
            ]:
                if tag in audio.tags:
                    del audio.tags[tag]
                audio.tags.add(frame(encoding=3, text=value))
            # Cover art
            if self.cover_art_selected:
                print(self.temp_path)
                with open(str(self.temp_path), 'rb') as img_file:
                    audio.tags.add(APIC(encoding=3, mime='image/png', type=3, desc='Cover Art', data=img_file.read()))
            audio.save()
            print(f"MP3 tags saved successfully for {self.file_name}")
            self.show_success_label()
            self.cleanup_temp_cover()
        except ID3NoHeaderError:
            audio = MP3(self.file_path)
            audio.add_tags()
            self.save_mp3_tags()
        except Exception as e:
            print(f"Error saving MP3 tags: {e}")

    def save_m4a_tags(self):
        try:
            audio = MP4(self.file_path)
            print(f"Loaded M4A tags for {self.file_name}")
            tags = self.get_tag_values()
            # Set tags
            audio["\xa9nam"] = tags["Song Name"]
            audio["\xa9ART"] = tags["Artist"]
            audio["\xa9alb"] = tags["Album"]
            audio["\xa9gen"] = tags["Genre"]
            audio["\xa9day"] = tags["Year"]
            # Cover art
            if self.cover_art_selected and self.temp_path:
                with open(self.temp_path, "rb") as img_file:
                    cover_data = img_file.read()
                    audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_PNG)]
            audio.save()
            print(f"M4A tags saved successfully for {self.file_name}")
            self.show_success_label()
            self.cleanup_temp_cover()
        except Exception as e:
            print(f"Error saving M4A tags: {e}")

    def save_flac_tags(self):
        try:
            audio = FLAC(self.file_path)
            print(f"Loaded FLAC tags for {self.file_name}")
            tags = self.get_tag_values()
            # Set tags
            audio["TITLE"] = tags["Song Name"]
            audio["ARTIST"] = tags["Artist"]
            audio["ALBUM"] = tags["Album"]
            audio["GENRE"] = tags["Genre"]
            audio["DATE"] = tags["Year"]
            # Cover art
            if self.cover_art_selected and self.temp_path:
                with open(self.temp_path, "rb") as img_file:
                    picture = Picture()
                    picture.type = 3  # Cover (front)
                    picture.mime = "image/png"
                    picture.data = img_file.read()
                    audio.clear_pictures()
                    audio.add_picture(picture)
            audio.save()
            print(f"FLAC tags saved successfully for {self.file_name}")
            self.show_success_label()
            self.cleanup_temp_cover()
        except Exception as e:
            print(f"Error saving FLAC tags: {e}")

    def save_ogg_tags(self):
        try:
            audio = OggVorbis(self.file_path)
            print(f"Loaded OGG tags for {self.file_name}")
            tags = self.get_tag_values()
            # Set tags
            audio["TITLE"] = tags["Song Name"]
            audio["ARTIST"] = tags["Artist"]
            audio["ALBUM"] = tags["Album"]
            audio["GENRE"] = tags["Genre"]
            audio["DATE"] = tags["Year"]
            audio.save()
            print(f"OGG tags saved successfully for {self.file_name}")
            self.show_success_label()
            self.cleanup_temp_cover()
        except Exception as e:
            print(f"Error saving OGG tags: {e}")

    def save_aac_tags(self):
        try:
            audio = AAC(self.file_path)
            print(f"Loaded AAC tags for {self.file_name}")
            tags = self.get_tag_values()
            # AAC files may use ID3 tags
            if not hasattr(audio, 'tags') or not audio.tags:
                audio.add_tags()
            # Remove and add tags
            for tag, frame, value in [
                ("TIT2", TIT2, tags["Song Name"]),
                ("TPE1", TPE1, tags["Artist"]),
                ("TALB", TALB, tags["Album"]),
                ("TCON", TCON, tags["Genre"]),
                ("TYER", TYER, tags["Year"]),
            ]:
                if tag in audio.tags:
                    del audio.tags[tag]
                audio.tags.add(frame(encoding=3, text=value))
            audio.save()
            print(f"AAC tags saved successfully for {self.file_name}")
            self.show_success_label()
            self.cleanup_temp_cover()
        except Exception as e:
            print(f"Error saving AAC tags: {e}")

    def save_wav_tags(self):
        try:
            audio = WAVE(self.file_path)
            print(f"Loaded WAV tags for {self.file_name}")
            tags = self.get_tag_values()
            # WAV files may use ID3 tags
            if not hasattr(audio, 'tags') or not audio.tags:
                audio.add_tags()
            # Remove and add tags
            for tag, frame, value in [
                ("TIT2", TIT2, tags["Song Name"]),
                ("TPE1", TPE1, tags["Artist"]),
                ("TALB", TALB, tags["Album"]),
                ("TCON", TCON, tags["Genre"]),
                ("TYER", TYER, tags["Year"]),
            ]:
                if tag in audio.tags:
                    del audio.tags[tag]
                audio.tags.add(frame(encoding=3, text=value))
            audio.save()
            print(f"WAV tags saved successfully for {self.file_name}")
            self.show_success_label()
            self.cleanup_temp_cover()
        except Exception as e:
            print(f"Error saving WAV tags: {e}")

    def hide_tag_options(self):
        # Destroy tag widgets if they exist
        for widget in getattr(self, 'tag_widgets', {}).values():
            widget.destroy()
        if hasattr(self, 'cover_art_button') and self.cover_art_button:
            self.cover_art_button.destroy()
        if hasattr(self, 'cover_art_label') and self.cover_art_label:
            self.cover_art_label.destroy()

    def choose_cover_art(self):
        art_path = filedialog.askopenfilename(
            title="Select Cover Art",
            filetypes=(("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"), ("All Files", "*.*"))
        )
        if art_path:
            self.cover_art_label.config(text=f"Selected cover art: {os.path.basename(art_path)}")
            img = Image.open(art_path)
            img.thumbnail((150, 150))
            self.cover_art_image = ImageTk.PhotoImage(img)
            self.cover_art_label.config(image=self.cover_art_image, text="")
            with tempfile.NamedTemporaryFile(prefix="ATE_", suffix=".png", delete=False) as tmp:
                self.cleanup_temp_cover()
                self.temp_path = tmp.name
                img.save(self.temp_path, format='PNG')
                print(f"Temporary cover art saved at: {self.temp_path}")
            self.cover_art_selected = True
        else:
            self.cover_art_label.config(image="", text="No cover art selected.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioTagEditor(root)
    root.mainloop()