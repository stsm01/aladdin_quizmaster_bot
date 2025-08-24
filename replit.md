# Overview

This is a Telegram Quiz Bot application designed for testing account manager knowledge. The system consists of a Telegram bot interface built with aiogram 3 and a FastAPI backend service. The bot presents multiple-choice questions to users, tracks their progress through quiz sessions, and provides immediate feedback with explanations. Administrators can import questions through a REST API, and the system maintains user statistics across multiple quiz attempts.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure
The application follows a modular architecture with clear separation of concerns:
- **Main Entry Points**: Three separate entry points (`main.py`, `run_api.py`, `run_bot.py`) allow running the full system or individual components
- **API Layer**: FastAPI-based REST API with separate admin and public endpoints
- **Bot Layer**: Telegram bot using aiogram 3 with FSM (Finite State Machine) for conversation flow
- **Core Layer**: Business logic, configuration, and data models
- **Storage Layer**: In-memory storage implementation for MVP functionality

## Deployment Architecture
The system is designed to run both the FastAPI server and Telegram bot concurrently using multiprocessing. The bot communicates with the API via HTTP requests to localhost, creating a decoupled architecture that allows for independent scaling and development.

## Bot Architecture
- **State Management**: Uses aiogram's FSM for managing conversation states (waiting for name, in quiz, viewing results)
- **Handler System**: Modular handler registration with separate modules for keyboards, texts, and states
- **API Communication**: Asynchronous HTTP requests to the local FastAPI server for all data operations

## API Architecture
- **Authentication**: Admin endpoints protected with API key authentication via headers
- **Route Organization**: Separated admin routes (question management) from public routes (quiz functionality)
- **Error Handling**: Structured error responses with appropriate HTTP status codes
- **CORS Support**: Enabled for potential web frontend integration

## Data Models
- **User Management**: Tracks Telegram users with registration timestamps
- **Question System**: Questions with multiple answer options, exactly one correct per question
- **Session Management**: Quiz sessions track user progress, question order, and scoring
- **Answer Tracking**: Individual answers linked to sessions for detailed analytics

## Storage Strategy
Uses in-memory storage for MVP implementation with structured data classes. This approach provides fast development and testing while maintaining a clear interface that can be easily replaced with a database implementation.

# External Dependencies

## Core Framework Dependencies
- **aiogram 3**: Modern Telegram Bot API framework for Python with async support and FSM capabilities
- **FastAPI**: Modern web framework for building APIs with automatic OpenAPI documentation
- **uvicorn**: ASGI server for running the FastAPI application
- **pydantic**: Data validation and settings management using Python type annotations

## Utility Dependencies
- **aiohttp**: Async HTTP client for bot-to-API communication
- **python-dotenv**: Environment variable management from .env files
- **structlog**: Structured logging for better debugging and monitoring

## Telegram Integration
- **Telegram Bot API**: Direct integration via aiogram for receiving messages and sending responses
- **Bot Token**: Requires bot registration with @BotFather to obtain authentication token

## Optional Database Support
- **PostgreSQL**: Mentioned in documentation for production deployment (currently using in-memory storage)
- **asyncpg**: PostgreSQL adapter for async Python applications
- **SQLAlchemy 2**: ORM for database operations
- **Alembic**: Database migration tool for schema management

## Infrastructure Requirements
- **Environment Variables**: Configuration through environment variables for tokens and settings
- **Port Management**: Configurable API port (default 8000) and host binding
- **Process Management**: Multiprocessing support for running bot and API concurrently