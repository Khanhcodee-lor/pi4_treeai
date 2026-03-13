import cv2


def extract_detections(results):
    detections = []
    if results is None:
        return detections

    boxes = getattr(results, "boxes", None)
    if boxes is None:
        return detections

    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        detections.append(
            {
                "label": results.names[cls_id],
                "confidence": round(conf, 4),
                "box": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                },
            }
        )

    return detections


def build_disease_list(detections):
    diseases = []
    seen = set()

    for item in detections:
        label = item["label"]
        if label in seen:
            continue
        seen.add(label)
        diseases.append(label)

    return diseases


def draw_boxes(frame, results):
    if results is None:
        return frame

    for item in extract_detections(results):
        x1 = item["box"]["x1"]
        y1 = item["box"]["y1"]
        x2 = item["box"]["x2"]
        y2 = item["box"]["y2"]
        label = f"{item['label']} {item['confidence']:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
        )
    return frame
