# মনবন্ধু (MonBondhu) - Community Health Navigator for Rural Bangladesh

[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26.svg)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6.svg)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

## Project Overview

**মনবন্ধু** (meaning "Mind Friend" in Bengali) is a widespread mental health and community healthcare platform designed specifically for rural Bangladesh. Built to address the unique challenges faced by rural communities, including limited internet access, cultural stigma around mental health, and scarce healthcare resources.

### The Story Behind MonBondhu

Meet **Hablu** - our leader who survived campus life, heartbreaks, and CGPA calculations, only to find himself at ShasthoTech Bangladesh Limited. His mission: build something that actually helps people in Bangladesh specially in the rural side while navigating corporate authority, etc.

### The Problem We Solve

In rural Bangladesh, mental health faces three massive barriers:

1. **Stigma**: "মন খারাপ? পাড়াপড়শি কী বলবে?" (What will the neighbors say?)
2. **Access**: The nearest psychiatrist is 80km away in the district hospital
3. **Awareness**: Most people don't know that anxiety is a medical condition, not a character flaw

Add to that maternal mortality, child malnutrition, seasonal diseases like dengue, and the reality of 2G networks - you have a real, messy, important problem.

---

## Features (9 Missions Completed)

### 1. Mental Health Check-In

- Daily mood tracking with culturally appropriate Bangla prompts
- Emotional state logging with simple scale
- Local data storage for privacy
- Longitudinal mental health journey view

### 2. Community Health Map

- Interactive mapping of healthcare facilities
- Geolocation-based proximity ranking
- Offline-capable fallback modes
- Simple list view for non-tech-savvy users

### 3. Anonymous Help Request

- Privacy-first, anonymous mental health support requests
- Offline queuing system
- Clear communication about next steps
- Cultural sensitivity in consent language

### 4. Seasonal Preventive Health Tips

- Contextual health advisory notifications
- Dengue prevention (monsoon months)
- Cold/flu management (winter)
- Diarrhea safety (summer)
- Region-specific communicable disease awareness

### 5. Maternal & Child Health Tracker

- Antenatal Care (ANC) visit reminders
- Child vaccination schedule management
- Bangladesh EPI calendar integration
- Privacy-first local data storage

### 6. Symptom Awareness Guide

- Educational interface for recognizing concerning symptoms
- Non-diagnostic language to prevent misinformation
- Culturally framed health-seeking behavior
- Emergency situation identification

### 7. Community Health Events

- Health camp and screening event management
- Blood donation drives and vaccination campaigns
- RSVP functionality and calendar integration
- Local event discovery

### 8. Volunteer Health Worker Directory

- Searchable directory of trained health workers
- Skill tags (mental health first aid, maternal health, etc.)
- Contact availability status
- Verification badges for trained professionals

### 9. Health Data Export for NGOs

- Aggregated, anonymized data export capabilities
- Privacy-compliant analytics
- Actionable insights for resource allocation
- Data minimization principles

---

## Technology Stack

### Backend

- **Framework**: Django 4.2
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Authentication**: Django Session Authentication
- **API**: Django REST Framework (for future expansion)

### Frontend

- **Markup**: HTML5 with Bengali Language Support
- **Styling**: CSS3 with Responsive Design
- **Interactivity**: Vanilla JavaScript (ES6+)
- **Icons**: Unicode Emojis for cross-platform compatibility

### Key Libraries & Tools

- **Pillow**: Image handling
- **LocalStorage**: Offline data persistence
- **Chart.js**: Data visualization (for mood tracking)
- **Eraser.io**: High-Level Design diagrams

---

## System Architecture

### High-Level Design (HLD)

[![HLD Diagram](https://eraser.io/images/placeholder-diagram.svg)](https://app.eraser.io/workspace/YOUR_WORKSPACE_ID?elements=chat%2Cfiles)

_Note: Replace the above link with your actual Eraser.io workspace URL_

### Database Schema

```sql
-- Core Models
- MoodCheckIn (mood, notes, created_at)
- HealthFacility (name, type, address, contact, hours)
- AnonymousHelpRequest (help_type, description, contact_preference)
- HealthWorker (name, phone, skills, location, availability)
- HealthEvent (title, type, date, location, organizer)
- PregnancyTracker (last_period_date, expected_delivery_date)
- ChildVaccination (child_name, birth_date, vaccines)
```
