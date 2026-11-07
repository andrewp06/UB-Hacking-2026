from character.joint import Joint
from character.guy import Guy
import character.circle
import character.rectangle


class JointInfo:
    def __init__(self, joint_id, joint:Joint):
        self.id = joint_id
        self.joint = joint
        self.body_a = joint.get_shape_a()
        self.body_b = joint.get_shape_b()


class GuyMorphology:
    def __init__(self, guy:Guy):
        self.__shapes = guy.get_shapes().copy()

        self.joints = [
            JointInfo(i, joint)
            for i, joint in enumerate(guy.get_joints())
        ]

        self.body_part_count = len(self.__shapes)
        self.joint_count = len(self.joints)


if __name__ == "__main__":

    head = character.circle.Circle(5)
    guy = Guy(head)
    leg = character.rectangle.Rectangle(2, 2)
    joint = Joint(head, leg, 0, 180)
    guy.add_joint(joint)
    guy.add_shape(leg)

    morphology = GuyMorphology(guy)

    print("Body parts:", morphology.body_part_count)
    print("Joints:", morphology.joint_count)

    for joint in morphology.joints:
        print(
            f"Joint {joint.id}: "
            f"{joint.body_a} -> {joint.body_b}"
        )