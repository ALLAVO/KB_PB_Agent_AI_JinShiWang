from PIL import Image

img = Image.open('/Users/hyungjuncho/Documents/SNU_BFA/KB_capstone/KB_PB_Agent_AI_JinShiWang/frontend/src/assets/client_profile/천소연2.png')
width, height = img.size
# 하단 20픽셀 제거 예시
cropped = img.crop((0, 0, width, height - 300))
cropped.save('/Users/hyungjuncho/Documents/SNU_BFA/KB_capstone/KB_PB_Agent_AI_JinShiWang/frontend/src/assets/client_profile/천소연.png')
# change anything