import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
import os
from datetime import datetime
import logging

from config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """이메일 발송 서비스 클래스"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME
        
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """
        이메일 발송
        
        Args:
            to_email: 수신자 이메일
            subject: 이메일 제목
            html_content: HTML 내용
            text_content: 텍스트 내용 (선택사항)
            attachments: 첨부파일 리스트 (선택사항)
                [{"filename": "file.pdf", "content": bytes, "content_type": "application/pdf"}]
        
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # 이메일 메시지 생성
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # HTML 내용 추가
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)
            
            # 텍스트 내용 추가 (있는 경우)
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)
            
            # 첨부파일 추가
            if attachments:
                for attachment in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment["content"])
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {attachment['filename']}"
                    )
                    message.attach(part)
            
            # SMTP 서버 연결 및 이메일 발송
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"이메일 발송 성공: {to_email} - {subject}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 발송 실패: {to_email} - {subject} - {str(e)}")
            return False
    
    def send_diagnosis_report(
        self,
        to_email: str,
        user_name: str,
        report_html: str,
        report_text: str,
        scores: dict
    ) -> bool:
        """
        진단 리포트 이메일 발송
        
        Args:
            to_email: 수신자 이메일
            user_name: 사용자 이름
            report_html: HTML 리포트 내용
            report_text: 텍스트 리포트 내용
            scores: 진단 점수 딕셔너리
        
        Returns:
            bool: 발송 성공 여부
        """
        subject = f"[MINDI] {user_name}님의 인지 기능 진단 결과 리포트"
        
        # 이메일 템플릿 적용
        email_html = self._create_diagnosis_email_template(
            user_name, report_html, scores
        )
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=email_html,
            text_content=report_text
        )
    
    def send_care_report(
        self,
        to_email: str,
        user_name: str,
        report_html: str,
        report_text: str,
        period: dict,
        conversation_count: int
    ) -> bool:
        """
        케어 리포트 이메일 발송
        
        Args:
            to_email: 수신자 이메일
            user_name: 사용자 이름
            report_html: HTML 리포트 내용
            report_text: 텍스트 리포트 내용
            period: 분석 기간
            conversation_count: 대화 횟수
        
        Returns:
            bool: 발송 성공 여부
        """
        subject = f"[MINDI] {user_name}님의 주간 케어 서비스 분석 리포트"
        
        # 이메일 템플릿 적용
        email_html = self._create_care_email_template(
            user_name, report_html, period, conversation_count
        )
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=email_html,
            text_content=report_text
        )
    
    def _create_diagnosis_email_template(
        self,
        user_name: str,
        report_html: str,
        scores: dict
    ) -> str:
        """진단 리포트 이메일 템플릿 생성"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>MINDI 진단 결과 리포트</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .score-summary {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 12px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">🧠 MINDI</div>
                <h1>인지 기능 진단 결과 리포트</h1>
                <p>생성일: {datetime.now().strftime('%Y년 %m월 %d일')}</p>
            </div>
            
            <div class="content">
                <h2>안녕하세요, {user_name}님!</h2>
                <p>MINDI 인지 기능 진단이 완료되었습니다. 아래 결과를 확인해 주세요.</p>
                
                <div class="score-summary">
                    <h3>📊 진단 점수 요약</h3>
                    <ul>
                        <li>음성 속도/억양 점수: {scores.get('acoustic_score_vit', 0)}</li>
                        <li>음성 안정성 점수: {scores.get('acoustic_score_lgbm', 0)}</li>
                        <li>언어 이해 점수: {scores.get('language_score_BERT', 0)}</li>
                        <li>의사소통 점수: {scores.get('language_score_gpt', 0)}</li>
                    </ul>
                </div>
                
                {report_html}
                
                <div class="footer">
                    <p>본 이메일은 MINDI 서비스에서 자동으로 발송되었습니다.</p>
                    <p>문의사항이 있으시면 고객센터로 연락해 주세요.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_care_email_template(
        self,
        user_name: str,
        report_html: str,
        period: dict,
        conversation_count: int
    ) -> str:
        """케어 리포트 이메일 템플릿 생성"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>MINDI 케어 서비스 분석</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .stats {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 12px;
                }}
                .logo {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">🧠 MINDI</div>
                <h1>주간 케어 서비스 분석 리포트</h1>
                <p>분석 기간: {period.get('start_date', '')} ~ {period.get('end_date', '')}</p>
            </div>
            
            <div class="content">
                <h2>안녕하세요, {user_name}님!</h2>
                <p>지난 주 MINDI와의 대화를 분석한 결과를 알려드립니다.</p>
                
                <div class="stats">
                    <h3>📈 주간 활동 요약</h3>
                    <ul>
                        <li>분석 기간: {period.get('start_date', '')} ~ {period.get('end_date', '')}</li>
                        <li>총 대화 횟수: {conversation_count}회</li>
                        <li>평균 일일 대화: {conversation_count // 7 if conversation_count > 0 else 0}회</li>
                    </ul>
                </div>
                
                {report_html}
                
                <div class="footer">
                    <p>본 이메일은 MINDI 서비스에서 자동으로 발송되었습니다.</p>
                    <p>문의사항이 있으시면 고객센터로 연락해 주세요.</p>
                </div>
            </div>
        </body>
        </html>
        """

# 전역 이메일 서비스 인스턴스
email_service = EmailService()
