# EduConnect: AI Personalized Learning Platform & Academic Tracker

An advanced academic optimization platform designed to track student performance, analyze learning profiles using Machine Learning, and dynamically generate personalized learning pathways based on historical performance indices.

---

## 📊 Data Flow Diagrams (DFD)

To provide clear documentation, the system's data flows are represented in three levels, organized vertically to maintain readability and structure.

### Level 0: Context Diagram
The highest-level view showing the boundaries of the EduConnect system, external entities, and data sinks.

```mermaid
graph TD
    %% Style Definitions
    classDef entity fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef system fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff;
    classDef storage fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff;

    %% Nodes
    Student["Student (Client App)"]:::entity
    System["EduConnect Core System"]:::system
    Database["Supabase Database (PostgreSQL)"]:::storage

    %% Flows
    Student -->|"User Registration / Login"| System
    Student -->|"Quiz Answers & Submissions"| System
    System -->|"Personalized Quizzes"| Student
    System -->|"Performance Analytics & Pathways"| Student

    System -->|"Read/Write User Profiles & Records"| Database
    Database -->|"Historical Quiz & User Data"| System
```

---

### Level 1: Process Overview (Functional DFD)
This diagram breaks down the system into core functional processes: Authentication, Quiz Generation, Analytics Engine, and Database Syncing.

```mermaid
graph TD
    %% Style Definitions
    classDef entity fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef process fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff;
    classDef storage fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff;

    %% Entities & Storage
    Student["Student Client"]:::entity
    DBUsers[("users Table")]:::storage
    DBResults[("quiz_results Table")]:::storage

    subgraph Processes
        P1["Process 1.0: <br> Authentication & Session Security"]:::process
        P2["Process 2.0: <br> Adaptive Quiz Generator"]:::process
        P3["Process 3.0: <br> Analytics & ML Pipeline"]:::process
    end

    %% Process 1.0 Flows
    Student -->|"1.1 Registration & Login Details"| P1
    P1 -->|"1.2 Read/Write credentials"| DBUsers
    P1 -->|"1.3 Return Signed JWT Session"| Student

    %% Process 2.0 Flows
    Student -->|"2.1 Request Quiz (Unit/Grand)"| P2
    P2 -->|"2.2 Load Syllabus Templates"| P2
    P2 -->|"2.3 Return Custom Question Payload"| Student

    %% Process 3.0 Flows
    Student -->|"3.1 Submit Answers & Time Taken"| P3
    P3 -->|"3.2 Insert Performance Records (JSONB)"| DBResults
    P3 -->|"3.3 Fetch Student History"| DBResults
    P3 -->|"3.4 Return Learning Path & Daily Indices"| Student
```

---

### Level 2: Detailed Data Flow (Analytics & ML Subsystem)
A granular look into the internal processing of user logs, mathematical index computations, and ML profiling.

```mermaid
graph TD
    %% Style Definitions
    classDef storage fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff;
    classDef calc fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff;
    classDef ml fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:#fff;
    classDef output fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;

    %% Data Source
    DBResults[("quiz_results Table")]:::storage

    %% Internal Calculations
    CalcAccuracy["Calculate Accuracy Index <br> AI = (Score / Max Score) * 100"]:::calc
    CalcSpeed["Calculate Speed Score <br> S = min(1.5, 45 / TimePerQuestion)"]:::calc
    CalcEfficiency["Calculate Efficiency Index <br> EI = AI * (45 / TimeRatio)"]:::calc

    %% ML Engine
    KMeansClust["K-Means Clusterer <br> (Group users into 3 clusters)"]:::ml
    GreedyPathway["Greedy Sorter <br> (Filter subtopics where ER >= 0.5)"]:::ml

    %% Final Outputs
    OutProfile["User Learner Profile <br> (Slow/Average/Quick)"]:::output
    OutPath["Hierarchical Pathway <br> (High-Priority Topics)"]:::output

    %% Connections
    DBResults -->|"Load raw scores & time logs"| CalcAccuracy
    DBResults -->|"Load response timestamps"| CalcSpeed
    
    CalcAccuracy --> CalcEfficiency
    CalcSpeed --> CalcEfficiency

    CalcAccuracy -->|"Accuracy parameter"| KMeansClust
    CalcSpeed -->|"Speed parameter"| KMeansClust
    KMeansClust -->|"Classified clusters"| OutProfile

    DBResults -->|"Extract error metrics"| GreedyPathway
    GreedyPathway -->|"Filtered study pathways"| OutPath
```

---

## 🎯 Project Objectives & Technical Implementation

EduConnect achieves four core objectives through targeted algorithms and mathematical relationships:

### Objective 1: Dynamic Learner Profiling
*   **Goal**: Classify students dynamically into profile groups (`Slow Learner`, `Average Learner`, and `Quick Learner`) based on their historical accuracy and response speed.
*   **Mathematical Modeling**:
    The platform calculates a composite **Performance Score** ($P_u$) for each user ($u$):
    $$P_u = 0.7 \cdot A_u + 0.3 \cdot (S_u - 1)$$
    Where:
    *   **Accuracy** ($A_u$) is defined as:
        $$A_u = \frac{\text{Correct Answers}}{\text{Total Questions}}$$
    *   **Speed Score** ($S_u$) is scaled relative to an ideal response time of 45 seconds per question:
        $$S_u = \min\left(1.5, \frac{45}{\text{Time per Question}}\right)$$
*   **Algorithm (K-Means Clustering)**:
    Using `scikit-learn`'s unsupervised **K-Means Clustering** algorithm with $K = 3$ clusters, the engine clusters the calculated $P_u$ metrics of all users. The cluster centers are sorted to assign labels:
    $$\text{Sorted Clusters: } C_0 < C_1 < C_2$$
    *   $C_0 \rightarrow$ **Slow Learner**
    *   $C_1 \rightarrow$ **Average Learner**
    *   $C_2 \rightarrow$ **Quick Learner**

### Objective 2: Personalized Learning Pathway Generation
*   **Goal**: Construct a structured, hierarchical remedial study plan highlighting weak syllabus subtopics.
*   **Mathematical Modeling**:
    For every subtopic ($s$) in topic ($t$) within a syllabus unit ($U$), the engine computes the student's **Error Rate** ($ER_s$):
    $$ER_s = 1 - \frac{\text{Correct Answers}_s}{\text{Total Questions}_s}$$
    Priority is classified dynamically:
    $$\text{Priority}(s) = \begin{cases} 
      \text{High-Priority} & \text{if } ER_s \ge 0.5 \\
      \text{Needs Review} & \text{if } 0 < ER_s < 0.5 
    \end{cases}$$
*   **Algorithm (Greedy Categorization)**:
    The DAA engine sequentially processes historical records to map performance. It builds a nested hierarchy:
    $$\text{Unit } \rightarrow \text{Topic } \rightarrow \text{Subtopics (filtered by priority)}$$
    This allows students to focus immediately on high-priority subtopics before progressing.

### Objective 3: Real-Time Performance & Efficiency Index Tracking
*   **Goal**: Calculate daily analytical indices showing the student's learning progression over time.
*   **Mathematical Modeling**:
    For each active day, the system computes the running averages of:
    *   **Accuracy Index** ($AI_d$):
        $$AI_d = \left( \frac{\sum \text{Score obtained}}{\sum \text{Max score possible}} \right) \times 100$$
    *   **Efficiency Index** ($EI_d$):
        $$EI_d = AI_d \times \left( \frac{45.0 \text{ seconds}}{\text{Avg. Time per Question}} \right) \times 100$$

### Objective 4: Adaptive Quiz Generation
*   **Goal**: Generate unit-wise and grand quizzes matching the syllabus structure and target difficulty configurations.
*   **Implementation**:
    The system reads template schemas and structures quizzes dynamically based on the student's profile, selecting questions corresponding to the required difficulty parameters.

---

## 📁 Internal Code Architecture

The backend codebase is structured into cohesive modules designed to separate business logic, database transactions, and mathematical computation:

*   **`main.py`**: The application entry point using **FastAPI**. It configures CORS middleware, registers routers, implements security dependency injection (`OAuth2PasswordBearer` and JWT validation), and exposes API endpoints for registration, quiz submission, and analytics.
*   **`database_service.py`**: Handles direct transactions to the Supabase PostgreSQL database using raw `psycopg2` queries. It features an automated database initializer (`init_db`) which executes DDL commands on startup to create the `users` and `quiz_results` schemas and indexes if they do not exist.
*   **`dashboard_engine.py`**: Implements the mathematical modeling engines. It runs the K-Means clustering algorithm for learner classification and computes daily accuracy and efficiency graphs.
*   **`analysis_engine.py`**: Analyzes the granular details of student answers, building hierarchical subtopic accuracy trees using a greedy linear traversal approach.
*   **`question_engine.py`**: Parses raw question banks stored as JSON templates, instantiates dynamic quiz variants, and scores student selections.

---

## 🛠️ Specialized Tools and Libraries Used

To keep the platform optimized, the application avoids heavy data science tools like Pandas, instead utilizing targeted libraries:

*   **`psycopg2-binary`**: Direct database connector for low-latency PostgreSQL communication.
*   **`scikit-learn`**: Utilized exclusively for running unsupervised `KMeans` clustering models.
*   **`python-jose[cryptography]`**: Provides JSON Web Token (JWT) signatures and token decoding.
*   **`passlib[bcrypt]`**: Secure password hashing algorithms using salted Bcrypt values.
*   **`pydantic`**: Fast schema validation and serialization for API requests and responses.
*   **`chart.js` & `react-chartjs-2`**: Client-side library to render accuracy and efficiency indices.

---

## 📝 Developer Note & Deployment Reflections

> [!NOTE]
> ### Context on Deployment Hurdles
> In the early development stages, several architectural decisions were made that created significant friction for deployment. Specifically, configuring the API base URL dependencies dynamically within a nested folder structure and attempting to bundle a Python backend and a React frontend under a single serverless Vercel deploy configuration led to recurrent deployment failures. 
>
> We failed to configure the package requirements properly (e.g., missing critical PostgreSQL libraries and trying to run compiling processes inside Vercel's serverless runtime environment). Because of this oversight, the application suffered from build failures on Vercel for a long time. We feel deeply embarrassed about these initial missteps, as they were basic configuration errors that could have been avoided with better foresight. 
> 
> However, we are pleased to state that the entire codebase logic, frontend React routing, and backend ML engine run flawlessly on local setups. By splitting the architecture—deploying the FastAPI backend to Render and the React static assets to Vercel—we have successfully resolved these errors.

---

## ❤️ Thank You

Thank you to everyone who took the time to read through this project's documentation and review our work. Your interest, feedback, and guidance help us build better, more resilient software!
