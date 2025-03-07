import os
import logging
import asyncio
import discord
from damgom_configure import DamgomConfigure
from damgom_audio import play_tts
import aiomysql


class DamgomFunction(DamgomConfigure):
    channel_id = os.getenv("DISCORD_CHANNEL_ID")

    def __init__(self):
        super().__init__()

        # Connection Pool
        self.pool = None

        # Register events and commands
        self.bot.event(self.on_ready)
        self.bot.event(self.on_message)
        self.bot.event(self.on_guild_join)
        self.bot.event(self.on_voice_state_update)
        self.bot.event(self.on_shutdown)

        # Display a list of Damgom bot commands
        @self.bot.tree.command(name="도움", description="담곰 봇의 명령어 리스트를 보여줘요.")
        async def help(interaction: discord.Interaction):
            logging.info("Reply commands")

            embed = discord.Embed(
                title="담곰 봇 명령어 목록",
                description="다음은 담곰 봇에서 사용할 수 있는 명령어들이예요.",
                color=discord.Color.blue()  # You can customize the color
            )

            # Add commands to the embed
            embed.add_field(name="/도움", value="담곰 봇의 명령어 리스트를 보여줘요.", inline=False)
            embed.add_field(name="/담곰_채널지정", value="담곰 봇 전용 채널을 지정해요.", inline=False)
            embed.add_field(name="/담곰_채널확인", value="담곰 봇 전용 채널을 확인해요.", inline=False)
            # Add other commands similarly...

            # Send the embed as a response
            await interaction.response.send_message(embed=embed)

        # Designate a Damgom dedicated channel
        @self.bot.tree.command(name="담곰_채널지정", description="담곰 봇 전용 채널을 지정해요.")
        @self.app_commands.describe(channel="전용 채널로 설정할 채널을 선택하세요.")
        async def designate(interaction: discord.Interaction, channel: discord.abc.GuildChannel):
            logging.info(f"Channel selected: {channel.name} ({channel.id})")
            await self.designate_server(interaction.guild, channel.id)

            logging.info("Damgom dedicated channel designated")
            await interaction.response.send_message(f"✅ '{channel.name}' 을(를) 담곰 전용채널로 설정했어요.")

        @self.bot.tree.command(name="담곰_채널확인", description="담곰 봇 전용 채널을 확인해요.")
        async def check(interaction: discord.Interaction):
            logging.info("check_designate server")
            result = await self.check_channel(interaction.guild)

            channel_id = result.get("channel_id") if result else None

            if channel_id:
                channel = interaction.guild.get_channel(channel_id)  # ID를 통해 채널 객체 가져오기
                if channel:
                    await interaction.response.send_message(f"✅ 담곰 전용 채널은 `{channel.name}` 이예요.")
                else:
                    await interaction.response.send_message("⚠️ 해당 채널을 찾을 수 없어요. 채널이 삭제되었을 수 있어요.")
            else:
                await interaction.response.send_message("⚠️ 아직 담곰 전용 채널이 지정되지 않았어요.")

    async def connect_db(self):
        """MySQL Connection Pool 생성"""
        self.pool = await aiomysql.create_pool(
            host="127.0.0.1",
            port=3306,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            charset="utf8",
            minsize=1,  # 최소 1개의 연결 유지
            maxsize=5,  # 최대 5개의 연결을 동적으로 할당
            autocommit=True
        )

    async def close_db(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def save_guild_info(self, guild):
        """새로운 서버 정보를 DB에 저장"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = """
                INSERT INTO serverinfo (server_id, name) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE name = VALUES(name);
                """
                await cursor.execute(sql, (guild.id, guild.name))

    async def designate_server(self, guild, channel_id):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                sql = """
                UPDATE serverinfo 
                SET channel_id = %s
                WHERE server_id = %s
                """
                await cursor.execute(sql, (channel_id, guild.id))

    async def fetch_server(self, guild):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM serverinfo WHERE server_id = %s", guild.id)
                return await cursor.fetchone()  # 결과 가져오기

    async def check_channel(self, guild):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT channel_id FROM serverinfo WHERE server_id = %s",
                                     guild.id)
                return await cursor.fetchone()

    async def get_saved_guilds(self):
        """DB에서 저장된 서버 ID 목록 가져오기"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT server_id FROM serverinfo")
                result = await cursor.fetchall()
                return {row[0] for row in result}  # 서버 ID를 집합(set)으로 반환

    async def sync_guilds(self):
        """현재 봇이 가입한 서버 목록과 DB를 동기화"""
        saved_guilds = await self.get_saved_guilds()

        # DB에 없는 서버를 저장
        for guild in self.bot.guilds:
            if guild.id not in saved_guilds:
                await self.save_guild_info(guild)
                print(f"✅ 동기화된 서버 추가됨: {guild.name} (ID: {guild.id})")

    async def setup_hook(self):
        try:
            await self.bot.tree.sync()  # 슬래시 명령어 동기화
            logging.info("Slash commands synced successfully!")
        except Exception as e:
            logging.error(f"Slash command sync failed: {e}")

    async def on_voice_state_update(self, member, before, after):
        if not before.channel and after.channel:
            if member.id == self.bot.user.id:
                await member.edit(deafen=True)

        if before.channel:
            if len(before.channel.members) == 1:
                if before.channel.guild.voice_client:
                    await before.channel.guild.voice_client.disconnect()

    # Connect the bot a Channel
    async def on_ready(self):
        await self.setup_hook()
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game("대기")
        )
        await self.connect_db()
        await self.sync_guilds()

    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        result = await self.check_channel(message.guild)
        if result:
            channel_id = result["channel_id"]

            if message.channel.id == channel_id:
                voice_channel = message.author.voice.channel

                if message.author.voice and voice_channel:
                    # 음성 채널에 없을 경우
                    if not message.guild.voice_client:
                        # 음성 채널 접속
                        await voice_channel.connect(self_deaf=True)
                        # 텍스트 음성으로 변환 후 출력
                        await play_tts(message)

                    else:
                        # 음성 채널에 있을 경우
                        voice_client = message.guild.voice_client
                        # 출력 중이지 않으면
                        if not voice_client.is_playing():
                            # 텍스트 음성으로 변환 후 출력
                            await play_tts(message)
                        # 출력 중이면
                        else:
                            # 대기 메시지 전송
                            await message.channel.send("⚠️ 이전 음성이 아직 끝나지 않았어요.", reference=message)
                            return

    async def on_guild_join(self, guild):
        await self.save_guild_info(guild)
        print(f"✅ 새로운 서버 추가됨: {guild.name} (ID: {guild.id})")

    async def on_shutdown(self):
        if self.pool:
            await self.close_db()
            await self.bot.close()

        loop = asyncio.get_event_loop()
        loop.stop()
