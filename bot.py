import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SUBMISSION_LOG_CHANNEL_ID = 1551665491884638278

class ApplyModal(discord.ui.Modal):
    def __init__(self, title_name: str, questions: list):
        super().__init__(title=title_name)
        self.questions = questions
        self.user_answers = {}

        for i, q in enumerate(questions):
            self.user_answers[f"q_{i}"] = discord.ui.inputText(
                label=q[:45], 
                style=discord.TextStyle.short, 
                required=True
            )
            self.add_item(self.user_answers[f"q_{i}"])

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"📋 تقديم جديد: {self.title}", color=discord.Color.blue())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        
        for i, q in enumerate(self.questions):
            embed.add_field(name=q, value=self.user_answers[f"q_{i}"].value, inline=False)
            
        view = ReviewActionView(interaction.user.id, self.title)
        
        channel = bot.get_channel(SUBMISSION_LOG_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed, view=view)
            
        await interaction.response.send_message("✅ تم إرسال تقديمك بنجاح للمراجعة!", ephemeral=True)

class ReviewActionView(discord.ui.View):
    def __init__(self, applicant_id: int, form_type: str):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.form_type = form_type

    @discord.ui.button(label="قبول ✅", style=discord.ButtonStyle.green, custom_id="accept_form")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReasonModal(self.applicant_id, self.form_type, True))

    @discord.ui.button(label="رفض ❌", style=discord.ButtonStyle.red, custom_id="reject_form")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReasonModal(self.applicant_id, self.form_type, False))

class ReasonModal(discord.ui.Modal):
    def __init__(self, applicant_id: int, form_type: str, is_accepted: bool):
        super().__init__(title="سبب القبول / الرفض")
        self.applicant_id = applicant_id
        self.form_type = form_type
        self.is_accepted = is_accepted

        self.reason_input = discord.ui.inputText(
            label="السبب", 
            style=discord.TextStyle.long, 
            placeholder="اكتب السبب هنا...", 
            required=True
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value
        applicant = interaction.guild.get_member(self.applicant_id)
        
        status_text = "تم قبولك 🎉" if self.is_accepted else "تم رفضك ❌"
        color = discord.Color.green() if self.is_accepted else discord.Color.red()
        
        embed = discord.Embed(title=f"نتيجة التقديم على ({self.form_type})", description=status_text, color=color)
        embed.add_field(name="السبب", value=reason, inline=False)
        
        if applicant:
            try:
                await applicant.send(embed=embed)
            except:
                pass
                
        new_embed = interaction.message.embeds[0]
        new_embed.add_field(name="الحالة", value=f"{status_text} بواسطة {interaction.user.mention}\n**السبب:** {reason}", inline=False)
        await interaction.message.edit(embed=new_embed, view=None)
        
        await interaction.response.send_message("✅ تم إرسال الرد بنجاح!", ephemeral=True)

class ApplySelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="مسار المبرمج", style=discord.ButtonStyle.blurple, emoji="💻", custom_id="apply_coder")
    async def coder_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        questions = [
            "اسمك الحقيقي:",
            "عمرك الحقيقي:",
            "خبراتك:",
            "لغاتك البرمجية:",
            "هل تقدر تسوي بوت في أسبوع؟"
        ]
        await interaction.response.send_modal(ApplyModal("مسار المبرمج", questions))

    @discord.ui.button(label="مسار المود", style=discord.ButtonStyle.blurple, emoji="🛡️", custom_id="apply_mod")
    async def mod_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        questions = [
            "اسمك الحقيقي:",
            "عمرك الحقيقي:",
            "خبراتك:",
            "لو صاحب البث تهاوش مع واحد من البث ايش تصرفك؟",
            "لو اثنين تهاوشوا و صاحب البث طلب منك تغير الكاتقوري ايش تصرفك؟",
            "أوامر المود:"
        ]
        await interaction.response.send_modal(ApplyModal("مسار المود", questions))

    @discord.ui.button(label="مسار الايفنت", style=discord.ButtonStyle.blurple, emoji="🎉", custom_id="apply_event")
    async def event_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        questions = [
            "اسمك الحقيقي:",
            "عمرك الحقيقي:",
            "خبراتك:",
            "هل تقدر تسوي بنر خلال ١٥ دقيقة؟",
            "كم تاخذ منك الصورة للايفنت؟"
        ]
        await interaction.response.send_modal(ApplyModal("مسار الايفنت", questions))

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تذكرة", style=discord.ButtonStyle.green, emoji="🎫", custom_id="open_ticket_main")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category_name = "🎯 | ====== Main ====== | 🎯"
        category = discord.utils.get(guild.categories, name=category_name)
        
        if not category:
            category = await guild.create_category(category_name)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        
        await interaction.response.send_message(f"✅ تم إنشاء تذكرتك: {channel.mention}", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def send_apply_panel(ctx):
    view = ApplySelectView()
    embed = discord.Embed(title="تقديمات الإدارة والمسارات", description="اضغط على الزر بالأسفل للتقديم في المسار المناسب لك.\n*(معك الوقت المحدد لكل اختبار، وممنوع وسائل المساعدة)*", color=discord.Color.dark_embed())
    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def send_ticket_panel(ctx):
    view = TicketView()
    embed = discord.Embed(title="نظام التذاكر", description="اضغط على الزر أدناه لفتح تذكرة جديدة والتواصل مع الإدارة.", color=discord.Color.green())
    await ctx.send(embed=embed, view=view)

# تشغيل البوت بأمان باستخدام متغيرات البيئة (Environment Variables)
bot.run(os.getenv("TOKEN"))
