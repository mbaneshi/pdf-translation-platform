# PDF Translation Platform - User Guide

## 🚀 Quick Start

Your PDF Translation Platform is now ready to use with enhanced features! Here's how to get started:

### 1. Access the Application
- Open your browser and go to: **http://localhost:3000**
- The application should load with a clean interface

### 2. Reset/Start New Document
- If you see an existing document, click **"New Document"** button in the top-right corner
- This will reset the interface to the upload state

### 3. Upload a PDF Document
- **Drag and drop** a PDF file onto the upload area, or
- **Click** the upload area to browse and select a file
- Supported: PDF files up to 100MB
- The system will validate and process your file

### 4. Choose Processing Mode
- **Enhanced Mode**: Advanced features with semantic analysis
- **Legacy Mode**: Standard processing
- Toggle between modes using the button in the header

## 🛠️ Advanced Features

### Custom API Configuration
1. Go to **Settings** (/settings)
2. Enter your **OpenAI API Key** for custom processing
3. Select your preferred **model** (GPT-4o, GPT-4o Mini, etc.)
4. Save settings for persistent use

### Custom Translation Prompts
1. In **Settings**, configure:
   - **System Prompt**: Define translator expertise
   - **Translation Prompt**: Specific translation instructions
   - **Style Prompt**: Style adaptation guidelines

### Theme Customization
- **Quick Toggle**: Use White/Black theme buttons in Settings
- **Persistent**: Theme choice is saved automatically

### Glossary Management
1. In **Settings**, add custom term pairs:
   - **English term** → **Persian translation**
   - Build your specialized vocabulary
   - Apply glossary during translation

### Sample Translation Style
1. Add **high-quality translation examples** in Settings
2. System will **adapt to your preferred style**
3. Consistent translations across documents

## 📝 Translation Workflow

### 1. Document Review
- After upload, the system will analyze and process your PDF
- View progress and document information
- Access the review interface

### 2. Side-by-Side Review
- **Original text** on the left
- **Persian translation** on the right
- **Character counts** for both versions
- **Copy to clipboard** functionality

### 3. Inline Editing
- Click **"Edit Translation"** to modify text
- **Real-time editing** with proper RTL direction
- **Save/Cancel/Reset** options

### 4. Translation Adjustment
- Click **"Adjust"** button for fine-tuning
- Provide **specific instructions** like:
  - "Make it more formal"
  - "Use simpler language"
  - "Emphasize philosophical terms"
- **Apply Glossary** button for terminology consistency

## 🔧 Technical Status

### ✅ Working Features
- ✅ API Health Check
- ✅ API Documentation
- ✅ Document Upload Endpoint
- ✅ User Settings Management
- ✅ Theme System
- ✅ File Upload Interface
- ✅ Error Handling & Feedback
- ✅ Side-by-Side Review Interface

### 🧪 Test Your Installation
Run the included test script:
```bash
./test-basic-functionality.sh
```

## 🎯 Recommended Usage

### For Academic Texts
1. Set quality level to **"High Quality"** or **"Premium"**
2. Add academic terminology to glossary
3. Use formal system prompts
4. Provide sample translations for consistency

### For Philosophical Content
1. Add philosophical concepts to glossary
2. Use specialized translation prompts
3. Enable format preservation
4. Review and adjust translations carefully

## 🐛 Troubleshooting

### Upload Issues
- Ensure file is a valid PDF
- Check file size (max 100MB)
- Try different files if one fails
- Check browser console for errors

### API Connection Issues
- Verify all Docker services are running: `docker-compose ps`
- Check API health: `curl https://apipdf.edcopo.info/health`
- Review network connectivity

### Translation Problems
- Verify OpenAI API key in settings
- Check API quota and billing
- Review custom prompts for clarity
- Try different quality levels

## 💡 Tips for Best Results

1. **Start Small**: Test with a short document first
2. **Build Glossary**: Add important terms gradually
3. **Use Samples**: Provide 2-3 high-quality translation examples
4. **Review & Adjust**: Use the adjustment feature for refinements
5. **Save Settings**: Configure once, use across all documents

## 🔄 Reset & Cleanup

If you need to start fresh:
1. Click **"New Document"** button
2. Clear browser localStorage if needed
3. Reset Docker containers: `docker-compose restart`

Your PDF Translation Platform is now ready for professional English-to-Persian document translation with full user control and customization!