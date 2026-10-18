import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SUBMISSION_LOG_CHANNEL_ID = 1551665491884638278

class ReasonModal(discord.ui.Modal):
    def __init__(self, applicant_id: int, form_type: str, accepted: bool):
        super().__init__(title="سبب القبول أو الرفض")
        self.applicant_id = applicant_id
        self.form_type = form_type
        self.accepted = accepted

        self.reason = discord.ui.TextInput(
            label="السبب / الملاحظات:",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        status_text = "تم قبوله ✅" if self.accepted else "تم رفضه ❌"
        await interaction.response.send_message(f"✅ تم تسجيل القرار ({status_text}) بنجاح.", ephemeral=True)

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

class ApplyModal(discord.ui.Modal):
    def __init__(self, title_name: str, questions: list):
        super().__init__(title=title_name)
        self.questions = questions
        self.user_answers = {}

        for i, q in enumerate(questions):
            text_input = discord.ui.TextInput(
                label=q[:45], 
                style=discord.TextStyle.short, 
                required=True
            )
            self.user_answers[f"q_{i}"] = text_input
            self.add_item(text_input)

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

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

# ضع التوكن الخاص بك هنا
bot.run("MTU1NTQ1NjIwNzMyMDI1NjU2Mw.Gs5cTX.9z7iU4y4dDb4gXsyEmbSc5GtVUkEM3ed5RRDCY")
