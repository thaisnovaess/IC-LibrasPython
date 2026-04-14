import cv2
import mediapipe as mp
from database.db import criar_tabelas, inserir_sinal, inserir_landmark

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

criar_tabelas()

nome_sinal = input("Digite o nome do sinal que vai gravar: ").strip()

gravando = False
sinal_id = None
frame_num = 0

print("Pressione G para começar a gravar")
print("Pressione S para parar de gravar")
print("Pressione ESC para sair")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Erro ao acessar câmera")
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_id, hand_landmarks in enumerate(result.multi_hand_landmarks):
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            if gravando and sinal_id is not None:
                for landmark_id, landmark in enumerate(hand_landmarks.landmark):
                    inserir_landmark(
                        sinal_id=sinal_id,
                        frame_num=frame_num,
                        hand_id=hand_id,
                        landmark_id=landmark_id,
                        x=landmark.x,
                        y=landmark.y,
                        z=landmark.z
                    )

    texto = "GRAVANDO" if gravando else "PARADO"
    cv2.putText(frame, texto, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("LIBRAS - Coleta", frame)

    tecla = cv2.waitKey(1) & 0xFF

    if tecla == 27:
        break

    elif tecla == ord('g'):
        gravando = True
        frame_num = 0
        sinal_id = inserir_sinal(nome_sinal, "coleta manual")
        print(f"Iniciando gravação do sinal: {nome_sinal} | ID: {sinal_id}")

    elif tecla == ord('s'):
        gravando = False
        sinal_id = None
        print("Gravação encerrada")

    if gravando:
        frame_num += 1

cap.release()
cv2.destroyAllWindows()