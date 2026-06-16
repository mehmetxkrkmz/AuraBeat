# AuraBeat
AuraBeat is a premium, fully cross-platform media downloader and player with a built-in 3D Parallax Visualizer and Particle Engine.

<br>

## 🇹🇷 Türkçe (Turkish)
AuraBeat; YouTube, Spotify, SoundCloud gibi platformlardan dilediğiniz içerikleri hem ses (MP3) hem de video (MP4) olarak en yüksek kalitede indirebilmenizi sağlayan, premium tasarımlı ve gelişmiş görselleştiriciye sahip modern bir medya yöneticisidir. Tamamen **Windows ve Linux** uyumlu olarak tasarlanmıştır.

### ✨ Özellikler
- **Hızlı İndirme:** İçerikleri kayıpsız formatlarda bilgisayarınıza indirir.
- **Akıllı Pano İzleyici:** Panoya (Clipboard) kopyaladığınız YouTube/Spotify linklerini algılayıp doğrudan indirme kutusuna yapıştırır.
- **Dahili Müzik Çalar & Görselleştirici:** 
  - **Glassmorphism:** Şık ve premium cam arka plan tasarımı.
  - **Sese Duyarlı Parçacık Efekti:** Müziğin temposuna (Özellikle bas vuruşlarına) duyarlı yıldız tozu animasyonları.
  - **3D Parallax Derinlik Efekti:** Farenizi hareket ettirdiğinizde oynatıcı menüsü ve arka plan arasında üç boyutlu bir derinlik hissi oluşur.
- **Evrensel Uyumluluk:** Her iki işletim sisteminde (Windows ve Linux) hiçbir kod değişikliği gerektirmeden çalışır.

### 🚀 Nasıl Kurulur ve Çalıştırılır?

AuraBeat hem **Windows 10 / Windows 11** hem de modern **Linux** dağıtımlarında (Ubuntu, Arch, Fedora vb.) sorunsuz çalışır.

**Gereksinimler:** 
- Python 3.10 veya daha yeni bir sürüm.
- Sisteminizde [FFmpeg](https://ffmpeg.org/) aracının kurulu olması gerekmektedir (İndirilen dosyaları işlemek ve oynatmak için hayati önem taşır).

#### Seçenek 1: Doğrudan Kaynak Koddan Çalıştırmak (Windows ve Linux)
Bu yöntem ile uygulamayı en hafif haliyle, doğrudan Python üzerinden çalıştırabilirsiniz.
1. Proje klasörünü bilgisayarınıza indirin (ZIP olarak indirin veya git ile klonlayın).
2. Klasörün içerisinde bir Komut Satırı (CMD) veya Terminal açın.
3. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
4. Uygulamayı başlatın:
   ```bash
   python main.py
   ```

#### Seçenek 2: Tıklanabilir Çalıştırılabilir Dosya Oluşturmak (Windows .exe veya Linux Executable)
Hiç Python koduyla uğraşmadan, arkadaşlarınızla paylaşabileceğiniz tek tıklamayla açılan bir uygulama dosyası (`.exe` veya Linux executable) çıkartmak isterseniz:
1. Terminal / CMD'yi açıp kütüphaneleri kurun:
   ```bash
   pip install -r requirements.txt
   ```
2. Otomatik derleme betiğini çalıştırın:
   ```bash
   python build.py
   ```
3. Tüm işlem bittiğinde projenin içinde oluşan `dist/AuraBeat` klasörünün içerisine girin.
   - **Windows Kullanıyorsanız:** Oradaki `AuraBeat.exe` dosyasına çift tıklayarak uygulamayı açabilirsiniz.
   - **Linux Kullanıyorsanız:** Oradaki `AuraBeat` isimli çalıştırılabilir dosyaya tıklayarak uygulamayı açabilirsiniz.

---

## 🇬🇧 English (İngilizce)
AuraBeat is a premium media downloader and player that allows you to download and enjoy high-quality media (MP3/MP4) from platforms like YouTube, Spotify, and SoundCloud. It is completely **Cross-Platform**, designed for both **Windows and Linux**.

### ✨ Features
- **Fast Downloading:** Lossless download options.
- **Smart Clipboard Monitor:** Automatically detects YouTube/Spotify links you copied and pastes them to the input field.
- **Built-in Player & Visualizer:**
  - **Glassmorphism UI:** Extremely premium frosted glass design.
  - **Audio Reactive Particle Engine:** Stardust and particle animations that react to the music's tempo and bass drops.
  - **3D Parallax Effect:** Creates a 3D depth illusion between the player interface and the background cover art as you move your mouse.
- **Universal Compatibility:** Runs flawlessly on both Windows and Linux without modifying the code.

### 🚀 How to Run and Build?

AuraBeat fully supports **Windows 10 / Windows 11** and modern **Linux** distributions (Ubuntu, Arch, Fedora, etc.).

**Requirements:** 
- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) installed and added to your system PATH.

#### Option 1: Run Directly (Windows & Linux)
1. Clone the repository or download it as a ZIP file.
2. Open a Command Prompt (CMD) or Terminal inside the folder.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the application:
   ```bash
   python main.py
   ```

#### Option 2: Build a Standalone Executable (Windows .exe or Linux Executable)
If you want a standalone application that you can share with others without requiring a Python installation:
1. Open Terminal / CMD and install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the automated build script:
   ```bash
   python build.py
   ```
3. After the build completes, go to the newly created `dist/AuraBeat/` directory.
   - **On Windows:** Double-click the `AuraBeat.exe` to run your app.
   - **On Linux:** Execute the standalone `AuraBeat` file to run your app.

---

**Developed by:** mehmet
