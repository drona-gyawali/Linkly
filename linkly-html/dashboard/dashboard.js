let userData = null;
let clickChart = null;

// Token management
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get("token");
if (token) {
localStorage.setItem("access_token", token);
window.history.replaceState({}, document.title, window.location.pathname);
}

const accessToken = localStorage.getItem("access_token");
if (!accessToken) {
window.location.href = "/login/login.html";
}

// API functions
async function fetchUserData() {
try {
    const response = await fetch('http://127.0.0.1:8000/me', {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'accept': 'application/json'
        }
    });
    
    if (!response.ok) throw new Error('Failed to fetch user data');
    
    userData = await response.json();
    updateUserProfile();
    updateUrlsList();
    updateQuickStats();
    loadAnalytics();
} catch (error) {
    console.error('Error fetching user data:', error);
    if (error.message.includes('401')) {
        logout();
    }
}
}

async function createShortUrl(originalUrl, expiry, utmParams = {}) {
try {
    const payload = {
        original_url: originalUrl,
        expiry: expiry
    };

    // Add UTM parameters if provided
    if (utmParams.source) payload.utm_source = utmParams.source;
    if (utmParams.medium) payload.utm_medium = utmParams.medium;
    if (utmParams.campaign) payload.utm_campaign = utmParams.campaign;

    const response = await fetch('http://127.0.0.1:8000/shorten', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
            'accept': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error('Failed to create short URL');

    const result = await response.json();
    return result;
} catch (error) {
    console.error('Error creating short URL:', error);
    throw error;
}
}

async function fetchAnalytics(shortId) {
try {
    const response = await fetch(`http://127.0.0.1:8000/analytics/${shortId}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'accept': 'application/json'
        }
    });
    
    if (!response.ok) throw new Error('Failed to fetch analytics');
    
    return await response.json();
} catch (error) {
    console.error('Error fetching analytics:', error);
    return null;
}
}

// Update functions
function updateUserProfile() {
document.getElementById('userName').textContent = userData.name || 'User';
document.getElementById('userEmail').textContent = userData.email || 'user@example.com';
document.getElementById('totalUrls').textContent = userData.urls?.length || 0;
}

function updateUrlsList() {
const urlsList = document.getElementById('urlsList');

if (!userData.urls || userData.urls.length === 0) {
    urlsList.innerHTML = `
        <div class="text-center text-gray-400 py-8">
            <i class="fas fa-link text-4xl mb-4"></i>
            <p class="text-lg">No URLs created yet</p>
            <p class="text-sm opacity-60">Start by creating your first short URL</p>
        </div>
    `;
    return;
}

urlsList.innerHTML = userData.urls.map(url => `
    <div class="url-item rounded-2xl p-4">
        <div class="flex items-center justify-between">
            <div class="flex-1">
                <div class="flex items-center space-x-3 mb-2">
                    <i class="fas fa-link text-blue-400"></i>
                    <span class="font-medium text-white">${url.short_id}</span>
                    <button onclick="copyToClipboard('http://127.0.0.1:8000/${url.short_id}')" class="text-gray-400 hover:text-blue-400 text-sm">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
                <p class="text-gray-400 text-sm truncate">${url.original_url}</p>
                <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                    <span><i class="fas fa-calendar mr-1"></i>${new Date(url.created_at * 1000).toLocaleDateString()}</span>
                    <span><i class="fas fa-clock mr-1"></i>Expires: ${url.expiry}s</span>
                </div>
            </div>
            <button onclick="showAnalytics('${url.short_id}')" class="glass-card-dark rounded-full px-4 py-2 hover:bg-blue-500/20 transition-colors">
                <i class="fas fa-chart-line text-blue-400 mr-2"></i>
                Analytics
            </button>
        </div>
    </div>
`).join('');
}

async function updateQuickStats() {
let totalClicks = 0;
let todayClicks = 0;
let activeUrls = 0;
let locations = new Set();

const today = new Date().toDateString();

for (const url of userData.urls) {
    const analytics = await fetchAnalytics(url.short_id);
    if (analytics) {
        totalClicks += analytics.clicks || 0;
        activeUrls++;
        
        if (analytics.click_details) {
            analytics.click_details.forEach(click => {
                const clickDate = new Date(click.timestamp).toDateString();
                if (clickDate === today) {
                    todayClicks++;
                }
                if (click.location) {
                    locations.add(click.location);
                }
            });
        }
    }
}

document.getElementById('totalClicks').textContent = totalClicks;
document.getElementById('todayClicks').textContent = todayClicks;
document.getElementById('activeUrls').textContent = activeUrls;
document.getElementById('uniqueLocations').textContent = locations.size;
}

async function loadAnalytics() {
const ctx = document.getElementById('clickChart').getContext('2d');

// Destroy existing chart
if (clickChart) {
    clickChart.destroy();
}

// Sample data for the chart
const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const data = [12, 19, 3, 5, 2, 3, 9];

clickChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [{
            label: 'Clicks',
            data: data,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    color: '#9ca3af'
                },
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            },
            x: {
                ticks: {
                    color: '#9ca3af'
                },
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            }
        }
    }
});

// Update locations list
await updateLocationsList();
}

async function updateLocationsList() {
const locationsList = document.getElementById('locationsList');
const locationMap = new Map();

for (const url of userData.urls) {
    const analytics = await fetchAnalytics(url.short_id);
    if (analytics && analytics.click_details) {
        analytics.click_details.forEach(click => {
            if (click.location) {
                locationMap.set(click.location, (locationMap.get(click.location) || 0) + 1);
            }
        });
    }
}

if (locationMap.size === 0) {
    locationsList.innerHTML = `
        <div class="text-center text-gray-400 py-4">
            <i class="fas fa-map-marker-alt text-2xl mb-2"></i>
            <p>No location data yet</p>
        </div>
    `;
    return;
}

const sortedLocations = Array.from(locationMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

locationsList.innerHTML = sortedLocations.map(([location, count]) => `
    <div class="location-badge rounded-xl p-3 flex items-center justify-between">
        <div class="flex items-center space-x-3">
            <i class="fas fa-map-marker-alt text-emerald-400"></i>
            <span class="text-white text-sm">${location}</span>
        </div>
        <span class="text-emerald-400 font-bold">${count}</span>
    </div>
`).join('');
}

async function showAnalytics(shortId) {
const analytics = await fetchAnalytics(shortId);
if (!analytics) return;

const modal = document.getElementById('analyticsModal');
const modalContent = document.getElementById('modalContent');

modalContent.innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div class="stats-card rounded-2xl p-6 text-center">
            <div class="text-4xl font-bold gradient-text mb-2">${analytics.clicks || 0}</div>
            <div class="text-sm text-gray-400 font-medium">Total Clicks</div>
        </div>
        <div class="stats-card rounded-2xl p-6 text-center">
            <div class="text-4xl font-bold text-emerald-400 mb-2">${analytics.finger_print?.length || 0}</div>
            <div class="text-sm text-gray-400 font-medium">Unique Visitors</div>
        </div>
    </div>

    <div class="glass-card-dark rounded-2xl p-6 mb-6">
        <h4 class="text-lg font-bold mb-4 text-white">Click Details</h4>
        <div class="space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
            ${analytics.click_details?.map(click => `
                <div class="border border-gray-700 rounded-lg p-3">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-blue-400 font-medium">${click.location || 'Unknown'}</span>
                        <span class="text-gray-400 text-sm">${new Date(click.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="text-gray-500 text-sm">
                        <div>IP: ${click.ip}</div>
                        <div>User Agent: ${click.user_agent}</div>
                        ${click.utm_source ? `<div class="mt-2 text-emerald-400">UTM Source: ${click.utm_source}</div>` : ''}
                        ${click.utm_medium ? `<div class="text-emerald-400">UTM Medium: ${click.utm_medium}</div>` : ''}
                        ${click.utm_campaign ? `<div class="text-emerald-400">UTM Campaign: ${click.utm_campaign}</div>` : ''}
                    </div>
                </div>
            `).join('') || '<p class="text-gray-400 text-center py-4">No click data available</p>'}
        </div>
    </div>
`;

modal.classList.remove('hidden');
}

function closeModal() {
document.getElementById('analyticsModal').classList.add('hidden');
}

function copyToClipboard(text) {
navigator.clipboard.writeText(text).then(() => {
    // Show a temporary success message
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg z-50';
    toast.textContent = 'Copied to clipboard!';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
});
}

function logout() {
localStorage.removeItem('access_token');
window.location.href = '/login/login.html';
}

// Close modal when clicking outside
document.getElementById('analyticsModal').addEventListener('click', (e) => {
if (e.target.id === 'analyticsModal') {
    closeModal();
}
});

// UTM Toggle functionality
document.getElementById('utmToggle').addEventListener('change', function() {
const utmSection = document.getElementById('utmSection');
if (this.checked) {
    utmSection.classList.remove('hidden');
    updateUrlPreview();
} else {
    utmSection.classList.add('hidden');
    updateUrlPreview();
}
});

// URL Preview functionality
function updateUrlPreview() {
const originalUrl = document.getElementById('originalUrl').value;
const utmToggle = document.getElementById('utmToggle').checked;
const preview = document.getElementById('urlPreview');

if (!originalUrl) {
    preview.textContent = 'Enter URL to see preview...';
    return;
}

let previewUrl = originalUrl;

if (utmToggle) {
    const utmSource = document.getElementById('utmSource').value;
    const utmMedium = document.getElementById('utmMedium').value;
    const utmCampaign = document.getElementById('utmCampaign').value;

    const params = new URLSearchParams();
    if (utmSource) params.append('utm_source', utmSource);
    if (utmMedium) params.append('utm_medium', utmMedium);
    if (utmCampaign) params.append('utm_campaign', utmCampaign);

    if (params.toString()) {
        previewUrl += (originalUrl.includes('?') ? '&' : '?') + params.toString();
    }
}

preview.textContent = previewUrl;
}

// Add event listeners for real-time preview updates
['originalUrl', 'utmSource', 'utmMedium', 'utmCampaign'].forEach(id => {
document.getElementById(id).addEventListener('input', updateUrlPreview);
});

// Form submission
document.getElementById('createUrlForm').addEventListener('submit', async function(e) {
e.preventDefault();

const createBtn = document.getElementById('createBtn');
const originalText = createBtn.innerHTML;

// Show loading state
createBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Creating...';
createBtn.disabled = true;

try {
    const originalUrl = document.getElementById('originalUrl').value;
    const expiry = parseInt(document.getElementById('expiry').value);
    const utmToggle = document.getElementById('utmToggle').checked;

    let utmParams = {};
    if (utmToggle) {
        utmParams = {
            source: document.getElementById('utmSource').value,
            medium: document.getElementById('utmMedium').value,
            campaign: document.getElementById('utmCampaign').value
        };
    }

    const result = await createShortUrl(originalUrl, expiry, utmParams);
    
    // Show success message
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg z-50 flex items-center space-x-2';
    toast.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>Short URL created successfully!</span>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);

    // Reset form
    document.getElementById('createUrlForm').reset();
    document.getElementById('utmSection').classList.add('hidden');
    document.getElementById('utmToggle').checked = false;
    updateUrlPreview();

    // Refresh user data to show new URL
    await fetchUserData();

} catch (error) {
    // Show error message
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg z-50 flex items-center space-x-2';
    toast.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        <span>Failed to create short URL. Please try again.</span>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
} finally {
    // Reset button state
    createBtn.innerHTML = originalText;
    createBtn.disabled = false;
}
});

// Initialize dashboard
fetchUserData();