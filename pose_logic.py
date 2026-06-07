
# ---------------- HELPER FUNCTIONS ----------------
import math

def safe(kp, name):
    for p in kp:
        if p["name"] == name:
            return p["x"], p["y"]
    return None, None

def back_straight(kp):
    ls = safe(kp, "left_shoulder")
    rs = safe(kp, "right_shoulder")
    lh = safe(kp, "left_hip")
    rh = safe(kp, "right_hip")
    nose = safe(kp, "nose")

    shoulders_above_hips = ls[1] < lh[1] and rs[1] < rh[1]
    torso_vertical = abs(ls[0] - lh[0]) < 0.12
    head_above_shoulders = nose[1] < ls[1]

    return shoulders_above_hips and torso_vertical and head_above_shoulders

def one_leg_forward(kp):
    la = safe(kp, "left_ankle")
    ra = safe(kp, "right_ankle")

    if None in la + ra:
        return False

    # feet should be apart (front-back stance)
    return abs(la[0] - ra[0]) > 0.18


def front_knee_bent(kp):
    lh = safe(kp, "left_hip")
    lk = safe(kp, "left_knee")
    la = safe(kp, "left_ankle")

    rh = safe(kp, "right_hip")
    rk = safe(kp, "right_knee")
    ra = safe(kp, "right_ankle")

    if None in lh + lk + la + rh + rk + ra:
        return False

    left_angle = angle(lh, lk, la)
    right_angle = angle(rh, rk, ra)

    # ✅ ACCEPT ANY CLEAR BEND
    return (left_angle < 165) or (right_angle < 165)



def looking_up(kp):
    nose = safe(kp, "nose")
    ls = safe(kp, "left_shoulder")
    rs = safe(kp, "right_shoulder")
    lh = safe(kp, "left_hip")
    rh = safe(kp, "right_hip")

    if None in nose + ls + rs + lh + rh:
        return False

    # 1️⃣ Head should not be down
    head_not_down = nose[1] < max(ls[1], rs[1]) + 0.05

    # 2️⃣ Torso upright (important!)
    torso_upright = abs(ls[0] - lh[0]) < 0.15 and abs(rs[0] - rh[0]) < 0.15

    return head_not_down and torso_upright




def hands_up(kp):
    lw = safe(kp, "left_wrist")
    rw = safe(kp, "right_wrist")
    ls = safe(kp, "left_shoulder")
    rs = safe(kp, "right_shoulder")

    if None in lw + rw + ls + rs:
        return False

    return lw[1] < ls[1] and rw[1] < rs[1]


def feet_together(kp):
    la = safe(kp, "left_ankle")
    ra = safe(kp, "right_ankle")

    if None in la + ra:
        return False

    return abs(la[0] - ra[0]) < 0.08

def knees_deep_bent(kp):
    lh = safe(kp, "left_hip")
    rh = safe(kp, "right_hip")
    lk = safe(kp, "left_knee")
    rk = safe(kp, "right_knee")

    # Hip should be close to knee level (chair depth)
    left_depth = abs(lh[1] - lk[1]) < 0.12
    right_depth = abs(rh[1] - rk[1]) < 0.12

    return left_depth or right_depth

def knee_bent(kp):
    lh = safe(kp, "left_hip")
    lk = safe(kp, "left_knee")

    if None in lh + lk:
        return False

    return lk[1] > lh[1]

def knee_angle(kp):
    lh = safe(kp, "left_hip")
    lk = safe(kp, "left_knee")
    la = safe(kp, "left_ankle")

    # approximate knee angle using Y positions
    return lk[1] - lh[1], la[1] - lk[1]


def knees_straight(kp):
    lh = safe(kp, "left_hip")
    lk = safe(kp, "left_knee")
    return lk[1] > lh[1] + 0.05


def knees_slightly_bent(kp):
    lh = safe(kp, "left_hip")
    lk = safe(kp, "left_knee")
    return lh[1] < lk[1] < lh[1] + 0.18
def angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    dot = ba[0]*bc[0] + ba[1]*bc[1]
    mag_ba = math.hypot(ba[0], ba[1])
    mag_bc = math.hypot(bc[0], bc[1])

    if mag_ba == 0 or mag_bc == 0:
        return 180

    cos_angle = dot / (mag_ba * mag_bc)
    cos_angle = max(-1, min(1, cos_angle))
    return math.degrees(math.acos(cos_angle))


def knees_deep_bent(kp):
    lh = safe(kp, "left_hip")
    lk = safe(kp, "left_knee")
    la = safe(kp, "left_ankle")

    rh = safe(kp, "right_hip")
    rk = safe(kp, "right_knee")
    ra = safe(kp, "right_ankle")

    if None in lh + lk + la + rh + rk + ra:
        return False

    left_angle = angle(lh, lk, la)
    right_angle = angle(rh, rk, ra)

    # Chair pose knee angle range
    return (90 <= left_angle <= 135) or (90 <= right_angle <= 135)



def is_standing(kp):
    nose = safe(kp, "nose")
    la = safe(kp, "left_ankle")
    ra = safe(kp, "right_ankle")
    lh = safe(kp, "left_hip")
    lk = safe(kp, "left_knee")

    # Ankles must be near bottom of body
    ankles_low = la[1] > 0.6 and ra[1] > 0.6

    # Hips must be clearly above knees
    hips_above_knees = lh[1] < lk[1] - 0.1

    # Body height should be large
    body_tall = (la[1] - nose[1]) > 0.5

    return ankles_low and hips_above_knees and body_tall


# ---------------- POSE FUNCTIONS ----------------
def distance(a, b):
    if None in a or None in b:
        return 999
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def tree_pose(kp, step):

    if step == 1:
        return is_standing(kp) and back_straight(kp), \
               "Stand straight on the floor."

    if step == 2:
        la = safe(kp, "left_ankle")
        ra = safe(kp, "right_ankle")
        lk = safe(kp, "left_knee")
        rk = safe(kp, "right_knee")

        if None in la + ra + lk + rk:
            return False, "Place one foot on the other leg."

        left_leg = distance(la, rk)
        right_leg = distance(ra, lk)

        return (
        left_leg < 0.15 or right_leg < 0.15,
         "Place that foot on the other leg."
    )


    if step == 3:
        lw = safe(kp, "left_wrist")
        rw = safe(kp, "right_wrist")
        return abs(lw[0] - rw[0]) < 0.1, \
               "Join your hands in front of chest."

    if step == 4:
        return back_straight(kp), "Keep your eyes steady."

    return False, "Adjust posture"


def chair_pose(kp, step):

    if step == 1:
        return is_standing(kp), "Stand straight on the floor."

    if step == 2:
        return knees_slightly_bent(kp) and is_standing(kp), \
               "Slowly bend your knees."

    if step == 3:
        return hands_up(kp), "Raise both hands up."

    if step == 4:
        return knees_deep_bent(kp), "Sit like on an invisible chair."

    if step == 5:
        return knees_deep_bent(kp) and back_straight(kp), \
               "Keep your back straight."

    return False, "Adjust posture"


def mountain_pose(kp, step):
    if step == 1:
        return back_straight(kp), "Stand straight on the floor."

    if step == 2:
        return feet_together(kp), "Keep your feet together."

    if step == 3:
        lw = safe(kp, "left_wrist")
        rw = safe(kp, "right_wrist")
        lh = safe(kp, "left_hip")
        rh = safe(kp, "right_hip")

        return abs(lw[1] - lh[1]) < 0.15 and abs(rw[1] - rh[1]) < 0.15, \
            "Keep your hands at your side."


    if step == 4:
        return back_straight(kp), "Lift your chest slightly."

    if step == 5:
        nose = safe(kp, "nose")
        ls = safe(kp, "left_shoulder")

    return nose[1] < ls[1], "Look straight ahead."

    return False, "Adjust posture"


def warrior1_pose(kp, step):

    # Step 1: Stand straight
    if step == 1:
        return is_standing(kp) and back_straight(kp), \
               "Stand straight first."

    # Step 2: Step one leg forward
    if step == 2:
        return one_leg_forward(kp), \
               "Step one leg forward."

    # Step 3: Bend front knee
    if step == 3:
        return front_knee_bent(kp), \
               "Bend the front knee."

    # Step 4: Raise both hands up
    if step == 4:
        return hands_up(kp), \
               "Raise both hands up."

    # Step 5: Look towards hands
    if step == 5:
        return hands_up(kp) and looking_up(kp) and one_leg_forward(kp), \
            "Look towards your hands."


    return False, "Adjust posture"

#lotus 
def is_sitting(kp):
    lh = safe(kp, "left_hip")
    lk = safe(kp, "left_knee")
    rh = safe(kp, "right_hip")
    rk = safe(kp, "right_knee")

    if None in lh + lk + rh + rk:
        return False

    # hips close to knees vertically → sitting
    return abs(lh[1] - lk[1]) < 0.15 and abs(rh[1] - rk[1]) < 0.15

def lotus_pose(kp, step):

    # Step 1: Sit on the floor
    if step == 1:
        return is_sitting(kp), "Sit on the floor."

    # ❌ For ALL next steps, user MUST be sitting
    if not is_sitting(kp):
        return False, "Please sit on the floor first."

    # Step 2: Right foot on left thigh
    if step == 2:
        ra = safe(kp, "right_ankle")
        lk = safe(kp, "left_knee")

        if None in ra + lk:
            return False, "Place right foot on left thigh."

        return ra[1] < lk[1], "Place right foot on left thigh."

    # Step 3: Left foot on right thigh
    if step == 3:
        la = safe(kp, "left_ankle")
        rk = safe(kp, "right_knee")

        if None in la + rk:
            return False, "Place left foot on right thigh."

        return la[1] < rk[1], "Place left foot on right thigh."

    # Step 4: Hands on knees
    if step == 4:
        lw = safe(kp, "left_wrist")
        rw = safe(kp, "right_wrist")
        lk = safe(kp, "left_knee")
        rk = safe(kp, "right_knee")

        return (
            abs(lw[1] - lk[1]) < 0.15 and abs(rw[1] - rk[1]) < 0.15,
            "Keep hands on knees."
        )

    return False, "Adjust posture"


def cobra_pose(kp, step):
    ls = safe(kp, "left_shoulder")
    lw = safe(kp, "left_wrist")

    if None in ls + lw:
        return False, "Adjust posture"

    if step == 1:
        return True, "Lie on your stomach on the floor."

    if step == 2:
        return True, "Keep your legs straight behind you."

    if step == 3:
        return lw[1] > ls[1], "Place your hands under your shoulders."

    if step == 4:
        return ls[1] < 0.55, "Slowly lift your chest up."

    if step == 5:
        return True, "Do not lift your hips."

    return False, "Adjust posture"


# ---------------- MAIN DISPATCH ----------------

def validate_pose(pose_name, step, keypoints):
    pose_map = {
        "Tree Pose": tree_pose,
        "Chair Pose": chair_pose,
        "Mountain Pose": mountain_pose,
        "Lotus Pose": lotus_pose,
        "Cobra Pose": cobra_pose,
        "Warrior I": warrior1_pose
    }

    if pose_name not in pose_map:
        return {"correct": False, "tip": "Pose not supported"}

    correct, tip = pose_map[pose_name](keypoints, step)
    return {"correct": bool(correct), "tip": tip}
