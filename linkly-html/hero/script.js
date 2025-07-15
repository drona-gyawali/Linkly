
const baseUrl = "http://127.0.0.1:8000/"

// Mobile menu toggle
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('hidden');
}

// Create short link functionality
async function createShortLink() {
    const urlInput = document.getElementById('urlInput');
    const customAlias = document.getElementById('customAlias');
    const resultSection = document.getElementById('resultSection');
    const shortUrl = document.getElementById('shortUrl');
    const originalUrl = urlInput.value.trim();
    const expireSelect = document.getElementById('expireSelect');
    const expiryDetails = document.getElementById('expiry-details')
    const expireValue = expireSelect.value;

    switch(expireValue) {
        case "1h":
            expiryDetails.textContent = "1 Hour"
            break;
        case "1d":
            expiryDetails.textContent = "1 Day"
            break;
        case "1w":
            expiryDetails.textContent= "1 Week"
            break;
        case "1m":
            expiryDetails.textContent= "1 Month"
            break;
        default: expiryDetails.textContent = "∞"

    }
    if (!originalUrl) {
        urlInput.value = 'Please enter a URL to shorten';
        setTimeout(() => {
            urlInput.value = ""
        }, 2000)
        return;
    }
    
    // add expire to seconds fx as our backend supports int type
    function expireToSeconds(expire) {
        if (!expire) return 0;

        const num = parseInt(expire.slice(0, -1));
        const unit = expire.slice(-1);

        switch (unit) {
            case 'h': return num * 3600;
            case 'd': return num * 86400;
            case 'w': return num * 604800;
            case 'm': return num * 2592000;
            default: return 0;
        }
    }

    const expirySeconds = expireToSeconds(expireValue);

    try {
        const response = await fetch(`${baseUrl}shorten`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({
                original_url: originalUrl,
                expiry: expirySeconds,
            }),
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const data = await response.json();
        shortUrl.textContent = data.short_url;
        resultSection.classList.remove('hidden');
        resultSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        urlInput.value = `Network Glitch Occur: Please input again after 5 seconds`
        setTimeout(() => {
            urlInput.value = "";
        }, 5000);
    }
}

// Fx responsible to delete the url
const delActions = document.getElementById("delete").addEventListener('click', delete_url);
async function delete_url() {
    const short_url = document.querySelector("#shortUrl");
    const full_url = short_url.textContent.trim();
    const short_id = full_url.split('/').pop();

    try {
        const response = await fetch(`${baseUrl}delete/${short_id}`, {
            method: 'GET',
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const data = await response.json();

        alert(data.message || "Link deleted successfully!");

        short_url.value = "";
        document.getElementById("resultSection").classList.add("hidden");
    } catch (error) {
        alert("Network glitch occurred. Please try again after 5 seconds.");
        console.error(error);
    }
}

// Copy to clipboard
function copyToClipboard() {
    const shortUrl = document.getElementById('shortUrl').textContent;
    navigator.clipboard.writeText(shortUrl).then(() => {
        alert('Link copied to clipboard!');
    });
}

document.getElementById("get-started").addEventListener("click", () => {
    window.location.href = '/signup/signup.html'
})

// Generate QR code
document.querySelector("#generate-qr").addEventListener('click', generateQR);
async function generateQR() {
    const short_url = document.querySelector("#shortUrl");
    if (!short_url) {
        alert("No shortened URL found.");
        return;
    }

    const full_url = short_url.textContent.trim();
    const short_id = full_url.split('/').pop();

    try {
        const response = await fetch(`${baseUrl}create-qr-code/${short_id}`, {
            method: "GET"
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        // Create <a> to download the file
        const a = document.createElement("a");
        a.href = url;
        a.download = `${short_id}_qrcode.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        // Clean up the blob URL
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error("QR Code download failed:", error);
        alert("Failed to download QR Code. Try again.");
    }
}


// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add parallax effect to orbs (throttled)
let ticking = false;

function updateParallax() {
    const scrolled = window.pageYOffset;
    const orbs = document.querySelectorAll('.orb');
    orbs.forEach((orb, index) => {
        const speed = 0.2 + (index * 0.1);
        orb.style.transform = `translateY(${scrolled * speed}px)`;
    });
    ticking = false;
}

window.addEventListener('scroll', () => {
    if (!ticking) {
        requestAnimationFrame(updateParallax);
        ticking = true;
    }
});

document.addEventListener("DOMContentLoaded", () => {
  const shareBtn = document.getElementById("share-btn");

  if (shareBtn) {
    shareBtn.addEventListener("click", () => {
      const shortUrlEl = document.getElementById("shortUrl");
      if (!shortUrlEl) return alert("Short URL not found.");
      
      const shortUrl = shortUrlEl.textContent.trim();
      const popup = document.createElement("div");
      popup.id = "share-popup";
      popup.className = "fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50";

      popup.innerHTML = `
        <div class="bg-white text-black p-6 rounded-xl w-80 space-y-4 shadow-xl relative">
          <h2 class="text-xl font-semibold text-center">Share this Link</h2>
          <div class="flex justify-around text-2xl">
            <a href="https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shortUrl)}" target="_blank" title="Share on Facebook">
              <i class="fab fa-facebook text-blue-600"></i>
            </a>
            <a href="https://twitter.com/intent/tweet?url=${encodeURIComponent(shortUrl)}" target="_blank" title="Share on Twitter">
              <i class="fab fa-twitter text-sky-500"></i>
            </a>
            <a href="https://wa.me/?text=${encodeURIComponent(shortUrl)}" target="_blank" title="Share on WhatsApp">
              <i class="fab fa-whatsapp text-green-500"></i>
            </a>
            <a href="https://t.me/share/url?url=${encodeURIComponent(shortUrl)}" target="_blank" title="Share on Telegram">
              <i class="fab fa-telegram text-blue-400"></i>
            </a>
          </div>
          <button id="close-share-popup" class="w-full mt-4 bg-pink-500 text-white py-2 px-4 rounded-lg hover:bg-pink-600">
            Close
          </button>
        </div>
      `;

      document.body.appendChild(popup);

      document.getElementById("close-share-popup").addEventListener("click", () => {
        popup.remove();
      });
    });
  }
});

