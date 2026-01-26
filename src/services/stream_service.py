import cv2

def draw_boxes(frame, results):
    if results is None:
        return frame

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = f"{results.names[cls_id]} {conf:.2f}"

        cv2.rectangle(frame, (x1,y1),(x2,y2),(0,255,0),2)
        cv2.putText(frame, label, (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,255,0), 1)
    return frame
