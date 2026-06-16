# AuraBeat
AuraBeat is a premium, cross-platform media downloader and player with a built-in 3D Parallax Visualizer and Particle Engine.

<br>

## 🇹🇷 Türkçe (Turkish)
AuraBeat; YouTube, Spotify, SoundCloud gibi platformlardan dilediğiniz içerikleri hem ses (MP3) hem de video (MP4) olarak en yüksek kalitede indirebilmenizi sağlayan, premium tasarımlı ve gelişmiş görselleştiriciye sahip modern bir medya yöneticisidir.

### ✨ Özellikler
- **Hızlı İndirme:** İçerikleri kayıpsız formatlarda bilgisayarınıza indirir.
- **Akıllı Pano İzleyici:** Panoya (Clipboard) kopyaladığınız YouTube/Spotify linklerini algılayıp doğrudan indirme kutusuna yapıştırır.
- **Dahili Müzik Çalar & Görselleştirici:** 
  - **Glassmorphism:** Şık ve premium cam arka plan tasarımı.
  - **Sese Duyarlı Parçacık Efekti:** Müziğin temposuna (Özellikle bas vuruşlarına) duyarlı yıldız tozu animasyonları.
  - **3D Parallax Derinlik Efekti:** Farenizi hareket ettirdiğinizde oynatıcı menüsü ve arka plan arasında üç boyutlu bir derinlik hissi oluşur.

### 🚀 Nasıl Kurulur ve Çalıştırılır?

AuraBeat'i çalıştırmak çok basittir. İster doğrudan Python kodu olarak çalıştırabilir, isterseniz de tek bir `AuraBeat.exe` haline getirebilirsiniz.

**Gereksinimler:** Python 3.10+ ve sisteminizde [FFmpeg](https://ffmpeg.org/) kurulu olması gerekmektedir. (FFmpeg dosyalarınızı dönüştürmek ve oynatmak için hayati önem taşır).

**Doğrudan Çalıştırmak İçin:**
1. Proje klasörünü indirin ve bir terminal açın.
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
3. Uygulamayı başlatın:
   ```bash
   python main.py
   ```

**Windows İçin Kendine Ait Bir .exe Çıkartmak İçin:**
Hiç Python koduyla uğraşmadan arkadaşlarınızla paylaşabileceğiniz bir `.exe` çıkartmak için:
1. Gerekli kütüphaneleri yükleyin: `pip install -r requirements.txt`
2. Derleme betiğini çalıştırın: `python build.py`
3. Tüm işlem bittiğinde `dist/AuraBeat` isimli klasörün içerisine girerek **AuraBeat.exe** uygulamanızı çalıştırabilirsiniz!

---

## 🇬🇧 English (İngilizce)
AuraBeat is a premium media downloader and player that allows you to download and enjoy high-quality media (MP3/MP4) from platforms like YouTube, Spotify, and SoundCloud.

### ✨ Features
- **Fast Downloading:** Lossless download options.
- **Smart Clipboard Monitor:** Automatically detects YouTube/Spotify links you copied and pastes them to the input field.
- **Built-in Player & Visualizer:**
  - **Glassmorphism UI:** Extremely premium frosted glass design.
  - **Audio Reactive Particle Engine:** Stardust and particle animations that react to the music's tempo and bass drops.
  - **3D Parallax Effect:** Creates a 3D depth illusion between the player interface and the background cover art as you move your mouse.

### 🚀 How to Run and Build?

**Requirements:** Python 3.10+ and [FFmpeg](https://ffmpeg.org/) installed on your system.

**To Run Directly:**
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the application:
   ```bash
   python main.py
   ```

**To Build a Standalone Executable (Windows/Linux):**
If you want a standalone executable (e.g. an `.exe` file on Windows) to share with others:
1. Install requirements: `pip install -r requirements.txt`
2. Run the build script: `python build.py`
3. After the build completes, your application will be inside the `dist/AuraBeat/` directory!

---

**Developed by:** mehmet
