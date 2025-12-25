from system.utils import get_float_option

def analyze_power_usage(months):
    """
    months: 最近 N 个月 MonthlyUsage 列表
    """
    tips = []

    if not months:
        return tips

    total_kwh = sum(m.kwh for m in months)
    avg_daily = total_kwh / (len(months) * 30)

    daily_warn = get_float_option("daily_kwh_warn", 6)

    if avg_daily > daily_warn:
        tips.append(
            f"您的日均用电量为 {avg_daily:.1f} kWh，高于系统推荐值 {daily_warn} kWh，建议减少高功率设备使用。"
        )

    # 电费增长分析
    if len(months) >= 2:
        last = months[0].kwh
        prev = months[1].kwh
        if last > prev * 1.2:
            tips.append(
                "本月用电量相比上月增长明显，建议检查空调、电热水器等大功率设备。"
            )

    if not tips:
        tips.append("您的用电情况整体平稳，请继续保持良好的用电习惯。")

    return tips
