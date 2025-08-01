# High-Level-Flowchart-Diagram for Automated Video Dubbing

This diagram represents the layered architecture of the video upload system with French-to-English caption translation.

```mermaid
graph TD
    subgraph Layered Architecture
        subgraph Presentation Layer
            A[User Clicks 'Upload Video'] --> B[File Selection Dialog]
            B -- Selected Video Path --> C{Video Upload & Initial Processing}
            C --> D[Video Player Display]
            D -- Displays --> E[Translated English Captions]
            D -- User Interaction --> F{Player Controls Pause/Resume}
            F --> D
        end

        subgraph Application Layer
            C --> G[Video & Audio Stream Processing]
            G --> H[Video Segmentation & Chunking]
            G --> I[Audio Extraction]
            I --> J{OpenAI Whisper Model API/Library}
            J --> O[Speech to Text - French]
            O --> K[French Transcription with Timestamps]
            K --> P[Language Translation - French to English]
            P --> L[English Translation]
            L --> M[Caption Synchronization]
            M --> E
        end

        subgraph Data Layer
            J --> N[Whisper Pre-trained Model Weights]
            N --> P
        end
    end
