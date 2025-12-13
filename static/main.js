let currentIssueData = null;

// UI: Preview Image on Upload
function previewImage(input) {
    const preview = document.getElementById('image-preview');
    const placeholder = document.getElementById('upload-placeholder');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.classList.remove('d-none');
            placeholder.classList.add('d-none');
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// Logic: Analyze Image
async function analyzeImage() {
    const fileInput = document.getElementById('imageInput');
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select an image first!");
        return;
    }

    // 1. Loading State
    const btn = document.getElementById('analyzeBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Scanning with AI...';

    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            alert("Error: " + data.error);
        } else {
            currentIssueData = data;
            populateDashboard(data);
        }

    } catch (error) {
        console.error('Error:', error);
        alert("Server connection failed.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Logic: Populate UI
function populateDashboard(data) {
    document.getElementById('analysis-result').classList.remove('d-none');
    document.getElementById('analysis-result').scrollIntoView({ behavior: 'smooth' });

    // Text Fields
    document.getElementById('ai-title').innerText = data.title;
    document.getElementById('ai-desc').innerText = data.description;
    document.getElementById('ai-dept').innerText = data.department;
    document.getElementById('ai-forecast').innerText = data.impact_forecast;
    document.getElementById('ai-evidence').innerText = data.required_evidence || "Evidence is clear.";

    // Score & Color Logic
    const score = data.severity_score;
    document.getElementById('ai-score').innerText = score;
    
    // Animate Circle & Set Color
    const circle = document.getElementById('score-circle');
    const percentage = score * 10;
    circle.setAttribute('stroke-dasharray', `${percentage}, 100`);

    // Dynamic Color Coding
    if (score >= 8) {
        circle.setAttribute('stroke', '#dc2626'); // Red
        document.getElementById('ai-score').classList.add('text-danger');
    } else if (score >= 5) {
        circle.setAttribute('stroke', '#f59e0b'); // Orange
        document.getElementById('ai-score').classList.add('text-warning');
    } else {
        circle.setAttribute('stroke', '#16a34a'); // Green
        document.getElementById('ai-score').classList.add('text-success');
    }

    // Risks List
    const risksList = document.getElementById('ai-risks');
    risksList.innerHTML = '';
    data.risks.forEach(risk => {
        const li = document.createElement('li');
        li.innerText = risk;
        risksList.appendChild(li);
    });
}

// Logic: Generate Complaint
async function generateLetter(type) {
    if (!currentIssueData) return;

    const letterCard = document.getElementById('letter-card');
    const letterContent = document.getElementById('letter-content');
    
    letterCard.classList.remove('d-none');
    letterCard.scrollIntoView({ behavior: 'smooth' });
    letterContent.innerText = "⚡ AI is writing your " + type + " draft...";

    try {
        const response = await fetch('/generate-complaint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                issue_data: currentIssueData,
                recipient_type: type
            })
        });

        const data = await response.json();
        letterContent.innerText = data.letter;
        
    } catch (error) {
        letterContent.innerText = "Error generating letter.";
    }
}

function copyToClipboard() {
    const text = document.getElementById('letter-content').innerText;
    navigator.clipboard.writeText(text);
    alert("Draft copied!");
}