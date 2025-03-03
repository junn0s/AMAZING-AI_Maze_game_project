# 🏆 KTB-21-Amazing | 내 손으로 만드는 나만의 스토리 미로 게임

<img width="1276" alt="image" src="https://github.com/user-attachments/assets/1fcd9816-d9dc-43ae-8f16-466597934ad2" />

**KTB-21-Amazing**은 사용자가 직접 만들어가는 미로 게임 프로젝트입니다.  
플레이어가 선택한 정보에 따라 **세계관과 NPC가 동적으로 생성**되며, 매번 새로운 경험을 제공합니다.

🚀 **이 프로젝트는 GitHub Actions + AWS CodeDeploy를 사용하여 자동화된 배포 시스템을 구축하였습니다.**

---

## 📌 **프로젝트 개요**
### 🎯 **목표**
- 내가 상상한 대로 스토리가 진행되는 미로 게임
- 내가 원하는 방식으로 NPC와 상호작용 가능
- 매번 새로운 환경과 선택지를 제공하여 몰입감 극대화

### 🕹 **게임 플레이 방식**
1. **사용자 입력** → 플레이어가 **이름, 직업, 분위기, 장소** 등을 입력  
2. **세계관 생성** → AI가 해당 정보를 기반으로 게임 환경을 동적으로 생성  
3. **NPC 상호작용** → NPC의 퀴즈를 풀며 진행 (+30초 / -30초)  
4. **미로 탈출 도전** → 제한 시간 내 탈출해야 성공!  

<p align="center">
  <img src="https://github.com/user-attachments/assets/a00a3374-16cb-4447-a9cd-121b654672e2" width="200">
  <img src="https://github.com/user-attachments/assets/cda423c7-40fb-4bf1-b903-9227f903a474" width="200">
  <img src="https://github.com/user-attachments/assets/5e3f3b82-91f5-44fd-90f7-d8ac5d0f86f5" width="200">
  <img src="https://github.com/user-attachments/assets/94e3c4a9-7625-498c-b733-27f4e6d333ea" width="200">
</p>


---

## 🏗 **기술 스택**
### 🎮 **프론트엔드**
- **React.js** + **Phaser.js** → 미로 게임 UI 및 상호작용 구현
- **TypeScript** → 정적 타입 시스템 적용
- **Axios** → 백엔드 API 통신

### ⚙️ **백엔드**
- **FastAPI** → API 서버 개발
- **GPT API / DALL·E API / LangChain** → AI 기반 게임 콘텐츠 생성

### ☁️ **클라우드 & 배포**
- **AWS EC2** → 서버 인프라 호스팅
- **AWS CodeDeploy + GitHub Actions** → CI/CD 자동화
---

## 👨‍💻 **Members**

<table>
    <tr align="center">
        <td><B>FrontEnd</B></td>
        <td><B>Backend</B></td>
        <td><B>AI</B></td>
        <td><B>AI</B></td>
        <td><B>Cloud</B></td>
        <td><B>Cloud</B></td>
    </tr>
    <tr align="center">
        <td><a href="https://github.com/jinaaaaaaaaaaaaa">Jina</a></td>
        <td><a href="https://github.com/jeli01">Jelly</a></td>
        <td><a href="https://github.com/junn0s">Milo</a></td>
        <td><a href="https://github.com/sophiness">Sophie</a></td>
        <td><a href="https://github.com/lunghyun">Mello</a></td>
        <td><a href="https://github.com/hyehae">Hannah</a></td>
    </tr>
    <tr align="center">
        <td>
            <img src="https://github.com/jinaaaaaaaaaaaaa.png" width = 100>
        </td>
        <td>
            <img src="https://github.com/jeli01.png" width = 100>
        </td>
        <td>
            <img src="https://github.com/junn0s.png" width = 100>
        </td>
        <td>
            <img src="https://github.com/sophiness.png" width = 100>
        </td>
        <td>
            <img src="https://github.com/lunghyun.png" width = 100>
        </td>
        <td>
            <img src="https://github.com/hyehae.png" width = 100>
        </td>
    </tr>
</table>

---

## 🗺️ **아키텍처**
![image](https://github.com/user-attachments/assets/799b5ae0-c00e-4c55-a34f-d767d04dddcb)

---

## 📂 **리포지토리 구성**
| 리포지토리 | 설명 |
|------------|-------------|
| [fe](https://github.com/KTB-21-Amazing/KTB-21-Amazing-FE) | 프론트엔드 (React + Phaser.js) |
| [be](https://github.com/KTB-21-Amazing/KTB-21-Amazing-BE) | 백엔드 (FastAPI + AI API) |

---

## 🚀 **배포 자동화 (CI/CD)**
이 프로젝트는 GitHub Actions 및 AWS CodeDeploy를 활용하여 자동으로 배포됩니다.

### 🔄 **배포 프로세스**
1. **GitHub에 코드 푸시** → `main` 브랜치 푸시 시 자동 트리거
2. **GitHub Actions 실행** → 테스트 및 빌드 수행
3. **AWS CodeDeploy 배포** → EC2 서버에 자동 업데이트

---

## 🎮 **게임 시작하기**
1. **[프론트엔드 실행](https://github.com/KTB-21-Amazing/fe)**
   ```bash
   git clone https://github.com/KTB-21-Amazing/fe.git
   cd fe
   npm install
   npm start
   ```

2. **[백엔드 실행](https://github.com/KTB-21-Amazing/be)**
   ```bash
   git clone https://github.com/KTB-21-Amazing/be.git
   cd be
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

---

## 🤝 **기여 방법**
- **Issue 등록** → 버그나 개선점을 [이슈](https://github.com/KTB-21-Amazing/issues)로 남겨주세요.
- **Pull Request** → 기능을 추가하고 싶다면 PR을 제출해주세요.

---

## 📧 **문의**
- **GitHub Discussions**: [프로젝트 Q&A](https://github.com/KTB-21-Amazing/discussions)
- **이메일**: ktb@example.com
