import cv2
import mediapipe as mp
import numpy as np

from database.db import criar_tabelas, inserir_sinal, inserir_landmark

# Configuração do MediaPipe para detectar mãos
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Abre a câmera do computador
camera = cv2.VideoCapture(0)

# Cria as tabelas do banco, caso ainda não existam
criar_tabelas()

nome_sinal = input("Digite o nome do sinal que vai gravar: ").strip()

gravando = False
sinal_id = None
numero_frame = 0

# Lista simples para guardar os dados antes de transformar em NumPy
dados_landmarks = []

print("Pressione G para começar a gravar")
print("Pressione S para parar de gravar")
print("Pressione ESC para sair")

while True:
    deu_certo, frame = camera.read()

    if not deu_certo:
        print("Não foi possível acessar a câmera")
        break

    # O OpenCV usa BGR, mas o MediaPipe usa RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Processa o frame para encontrar a mão
    resultado = hands.process(frame_rgb)

    if resultado.multi_hand_landmarks:
        for id_mao, pontos_mao in enumerate(resultado.multi_hand_landmarks):

            # Desenha os pontos e ligações da mão na tela
            mp_draw.draw_landmarks(
                frame,
                pontos_mao,
                mp_hands.HAND_CONNECTIONS
            )

            # Se estiver gravando, salva os pontos da mão
            if gravando and sinal_id is not None:
                for id_ponto, ponto in enumerate(pontos_mao.landmark):

                    # Guarda os dados em uma lista
                    dados_landmarks.append([
                        sinal_id,
                        numero_frame,
                        id_mao,
                        id_ponto,
                        ponto.x,
                        ponto.y,
                        ponto.z
                    ])

                    # Salva os mesmos dados no banco
                    inserir_landmark(
                        sinal_id=sinal_id,
                        frame_num=numero_frame,
                        hand_id=id_mao,
                        landmark_id=id_ponto,
                        x=ponto.x,
                        y=ponto.y,
                        z=ponto.z
                    )

    status = "GRAVANDO" if gravando else "PARADO"

    cv2.putText(
        frame,
        status,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("LIBRAS - Coleta", frame)

    tecla = cv2.waitKey(1) & 0xFF

    if tecla == 27:  # ESC
        break

    elif tecla == ord('g'):
        gravando = True
        numero_frame = 0
        sinal_id = inserir_sinal(nome_sinal, "coleta manual")

        print(f"Gravando o sinal: {nome_sinal} | ID: {sinal_id}")

    elif tecla == ord('s'):
        gravando = False
        sinal_id = None

        print("Gravação finalizada")

    if gravando:
        numero_frame += 1

# Transforma a lista de dados em um array NumPy
array_landmarks = np.array(dados_landmarks)

print("Array criado com NumPy:")
print(array_landmarks)
print(type(array_landmarks))

camera.release()
cv2.destroyAllWindows()