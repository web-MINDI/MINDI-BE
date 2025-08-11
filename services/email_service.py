import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
import os
from datetime import datetime, timedelta
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
        self.from_email = settings.FROM_EMAIL if settings.FROM_EMAIL else settings.SMTP_USERNAME
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
            try:
                # 기본 SSL 컨텍스트로 시도
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(message)
            except ssl.SSLError as ssl_error:
                # SSL 인증서 문제가 있는 경우 안전하지 않은 방법 사용
                logger.warning(f"SSL 인증서 검증 실패, 안전하지 않은 연결로 재시도: {ssl_error}")
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
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
        evaluate_good_list: List[str],
        evaluate_bad_list: List[str],
        result_good_list: List[str],
        result_bad_list: List[str],
        scores: dict
    ) -> bool:
        """
        진단 리포트 이메일 발송
        
        Args:
            to_email: 수신자 이메일
            user_name: 사용자 이름
            evaluate_good_list: 잘하고 있어요 리스트
            evaluate_bad_list: 노력이 필요해요 리스트
            result_good_list: 잘하고 있어요 결과 리스트
            result_bad_list: 노력이 필요해요 결과 리스트
            scores: 진단 점수 딕셔너리
        
        Returns:
            bool: 발송 성공 여부
        """
        subject = f"[MINDI] {user_name}님의 인지 기능 진단 결과 리포트"
        
        # 이메일 템플릿 적용
        email_html = self._create_diagnosis_email_template(
            user_name, evaluate_good_list, evaluate_bad_list, result_good_list, result_bad_list, scores
        )
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=email_html
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
        evaluate_good_list: List[str],
        evaluate_bad_list: List[str],
        result_good_list: List[str],
        result_bad_list: List[str],
        scores: dict
    ) -> str:
        """진단 리포트 이메일 템플릿 생성"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # HTML 템플릿 파일 읽기
        template_path = os.path.join(os.path.dirname(__file__), "email_template.html")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            logger.error(f"이메일 템플릿 파일을 찾을 수 없습니다: {template_path}")
            return self._create_fallback_diagnosis_template(
                user_name, evaluate_good_list, evaluate_bad_list, 
                result_good_list, result_bad_list, scores
            )
        
        # 동적 데이터로 템플릿 치환
        email_html = template_content
        
        # 기본 정보 치환
        email_html = email_html.replace("{{CURRENT_DATE}}", current_date)
        
        # 잘하고 있어요 섹션 처리
        if evaluate_good_list:
            evaluate_discription = ""
            for item in evaluate_good_list:
                evaluate_discription += f"{item}<br>"
            
            result_discription = ""
            for item in result_good_list:
                result_discription += f"{item}<br>"
            
            # 섹션 활성화
            email_html = email_html.replace("{{#GOOD_LIST}}", "")
            email_html = email_html.replace("{{/GOOD_LIST}}", "")

            email_html = email_html.replace("{{#EVALUATE_GOOD_LIST}}", "")
            email_html = email_html.replace("{{/EVALUATE_GOOD_LIST}}", "")
            email_html = email_html.replace("{{.}}", evaluate_discription)
            
            email_html = email_html.replace("{{#RESULT_GOOD_LIST}}", "")
            email_html = email_html.replace("{{/RESULT_GOOD_LIST}}", "")
            email_html = email_html.replace("{{.}}", result_discription)
        else:
            # 섹션 비활성화
            email_html = email_html.replace("{{#GOOD_LIST}}", "<!--")
            email_html = email_html.replace("{{/GOOD_LIST}}", "-->")
        
        # 노력이 필요해요 섹션 처리
        if evaluate_bad_list:
            evaluate_discription = ""
            for item in evaluate_bad_list:
                evaluate_discription += f"{item}<br>"
            
            result_discription = ""
            for item in result_bad_list:
                result_discription += f"{item}<br>"
            
            # 섹션 활성화
            email_html = email_html.replace("{{#BAD_LIST}}", "")
            email_html = email_html.replace("{{/BAD_LIST}}", "")

            email_html = email_html.replace("{{#EVALUATE_BAD_LIST}}", "")
            email_html = email_html.replace("{{/EVALUATE_BAD_LIST}}", "")
            email_html = email_html.replace("{{.}}", evaluate_discription)
            
            email_html = email_html.replace("{{#RESULT_BAD_LIST}}", "")
            email_html = email_html.replace("{{/RESULT_BAD_LIST}}", "")
            email_html = email_html.replace("{{.}}", result_discription)
        else:
            # 섹션 비활성화
            email_html = email_html.replace("{{#BAD_LIST}}", "<!--")
            email_html = email_html.replace("{{/BAD_LIST}}", "-->")

        # 차트 날짜 치환
        chart_labels = [datetime.now() - timedelta(days=i) for i in range(6, -1, -1)]
        chart_labels_html = ""
        for label in chart_labels:
            chart_labels_html += f"<td class='chart-label'>{label.strftime('%m/%d')}</td>"
        email_html = email_html.replace("{{CHART_LABELS}}", chart_labels_html)
        
        return email_html
    
    def _create_fallback_diagnosis_template(
        self,
        user_name: str,
        evaluate_good_list: List[str],
        evaluate_bad_list: List[str],
        result_good_list: List[str],
        result_bad_list: List[str],
        scores: dict
    ) -> str:
        """템플릿 파일이 없을 때 사용할 기본 템플릿"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>MINDI 진단 결과</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #17b26a; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .good {{ background: #e9f8ef; padding: 15px; margin: 10px 0; border-left: 4px solid #17b26a; }}
                .bad {{ background: #fdecec; padding: 15px; margin: 10px 0; border-left: 4px solid #ef4444; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🧠 MINDI 인지 기능 진단 결과</h1>
                <p>{user_name}님의 진단 결과입니다</p>
                <p>진단일: {current_date}</p>
            </div>
            
            <div class="content">
                <h2>진단 결과 분석</h2>
                
                <div class="good">
                    <h3>잘하고 있어요! ✅</h3>
                    <ul>
                        {''.join([f'<li>{item}</li>' for item in evaluate_good_list])}
                    </ul>
                </div>
                
                <div class="bad">
                    <h3>노력이 필요해요! ⚠️</h3>
                    <ul>
                        {''.join([f'<li>{item}</li>' for item in evaluate_bad_list])}
                    </ul>
                </div>
                
                <h2>점수 결과</h2>
                <ul>
                    {''.join([f'<li>{key}: {value}</li>' for key, value in scores.items()])}
                </ul>
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
