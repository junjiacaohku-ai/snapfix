"""Deterministic offline safety gate for the PRD F3 high-risk categories."""
from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class SafetyVerdict:
    refused: bool
    category: str | None = None
    reason: str = ""
    advice: str = ""


def _has(pattern, text):
    return re.search(pattern, text) is not None


def check(*texts: str | None) -> SafetyVerdict:
    text = unicodedata.normalize('NFKC', ' '.join(t for t in texts if t)).lower()
    text = text.translate(str.maketrans('電爐壓閥內維線燒煙脹氣牆劑鋰鍋', '电炉压阀内维线烧烟胀气墙剂锂锅'))
    internal = _has(r'内部|拆|开盖|接线|线路|电线|电路板|维修|修理|\b(internal|inside|wiring|rewire|disassembl\w*|repair|open)\b', text)
    appliance = _has(r'电磁炉|电陶炉|烤箱|电饭煲|电暖器|\b(induction|oven|hob|cooktop|space heater)\b', text)
    pressure = _has(r'锅炉|蒸汽|压力阀|泄压阀|安全阀|\b(boiler|steam|pressure valve|relief valve)\b', text)
    pressure_work = _has(r'拆|调|换|堵|维修|修理|\b(remove|replace|adjust|block|repair|dismantle)\b', text)
    burning = _has(r'烧焦|冒烟|火花|烧熔|\b(smok\w*|scorch\w*|burnt|sparking)\b', text)
    electrical = _has(r'插座|插头|电线|电器|配电|电路|\b(socket|outlet|plug|wire|wiring|electrical|power strip)\b', text)
    electrical_work = _has(r'更换|改线|接线|拆|维修|修理|\b(repair|replace|rewire|install)\b', text)
    chemical = _has(r'漂白水|漂白剂|氨水|通渠水|洁厕|\b(bleach|ammonia|drain cleaner|acid)\b', text)
    mixing = _has(r'混|一起|兑|加上|\b(mix\w*|combin\w*|together)\b', text)
    rules = [
        ('电气冒烟或烧焦', burning and electrical, '电气烧焦、冒烟或打火可能导致触电或火灾。'),
        ('市电线路拆修', electrical and electrical_work, '插座和电气线路拆修可能造成触电或火灾。'),
        ('市电设备内部维修', internal and appliance, '设备内部涉及市电和储能元件，不提供开盖、接线或拆修步骤。'),
        ('受压设备拆装', pressure and pressure_work, '受压设备及安全阀的拆装可能释放高温介质或破坏保护装置。'),
        ('微波炉高压电容', _has(r'微波炉|高压电容|磁控管|\b(microwave|capacitor|magnetron)\b', text), '微波炉内部可能保留危险电量。'),
        ('燃气设备', _has(r'燃气|煤气|天然气|\bgas\b', text), '燃气异常或拆装有泄漏、火灾和中毒风险。'),
        ('制冷剂回路', _has(r'冷媒|雪种|制冷剂|加氟|空调不冷|\b(refrigerant|freon)\b', text), '制冷剂回路涉及压力和专业设备。'),
        ('锂电池拆解', _has(r'电池拆解|电芯|18650|拆电池|鼓包|膨胀电池|\b(lithium|battery pack|swollen battery)\b', text), '受损锂电池或拆解电芯有起火风险。'),
        ('市电配电', _has(r'配电箱|电闸|强电|漏电开关|总闸|改电路|\b(breaker|mains|rewire)\b', text), '市电线路作业有触电风险。'),
        ('电热水器内部', _has(r'电热水器|加热管|加热棒|\b(heating element|water heater element)\b', text), '电热水器内部同时涉及水路和市电。'),
        ('高空作业', _has(r'空调外机|窗外|高空|窗台外|外墙|\boutdoor unit\b', text), '高空或外墙作业存在坠落风险。'),
        ('电焊或切割', _has(r'电焊|切割|角磨机|\b(welding|angle grinder)\b', text), '电焊和切割涉及火花、高温和机械伤害。'),
        ('化学品混用', chemical and mixing, '混用清洁剂可能产生有毒气体。'),
        ('石棉', _has(r'石棉|\basbestos\b', text), '扰动石棉会释放有害纤维。'),
        ('承重结构', _has(r'承重墙|承重柱|拆墙|打墙|\bload[- ]bearing\b', text), '结构改动需要专业评估。'),
        ('电梯', _has(r'电梯|扶梯|\b(elevator|escalator|lift controller)\b', text), '电梯维修需要专业人员处理。'),
    ]
    for category, matched, reason in rules:
        if matched:
            return SafetyVerdict(True, category, reason,
                                 '停止自行检修，联系品牌售后或合资格维修人员。如有烟火或泄漏危险，先远离现场并联系当地紧急服务。')
    return SafetyVerdict(False)
