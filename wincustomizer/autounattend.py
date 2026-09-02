"""
Autounattend Generator Module for WinCustomizer
Generates valid Windows unattended setup answer files (autounattend.xml).
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any, Optional

class AutounattendGenerator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def generate_xml(self) -> str:
        """
        Generates autounattend.xml XML string based on configuration.
        """
        username = self.config.get("username", "User")
        password = self.config.get("password", "")
        computer_name = self.config.get("computer_name", "WinCustom-PC")
        language = self.config.get("language", "en-US")
        timezone = self.config.get("timezone", "UTC")
        auto_logon = self.config.get("auto_logon", True)
        skip_oobe = self.config.get("skip_oobe", True)

        xml_template = fr"""<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
    <settings pass="windowsPE">
        <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <SetupUILanguage>
                <UILanguage>{language}</UILanguage>
            </SetupUILanguage>
            <InputLocale>{language}</InputLocale>
            <SystemLocale>{language}</SystemLocale>
            <UserLocale>{language}</UserLocale>
            <UILanguage>{language}</UILanguage>
        </component>
        <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <UserData>
                <AcceptEula>true</AcceptEula>
            </UserData>
            <RunSynchronous>
                <!-- Bypass Windows 11 hardware checks during setup -->
                <RunSynchronousCommand wcm:action="add">
                    <Order>1</Order>
                    <Path>reg add "HKLM\SYSTEM\Setup\LabConfig" /v BypassTPMCheck /t REG_DWORD /d 1 /f</Path>
                </RunSynchronousCommand>
                <RunSynchronousCommand wcm:action="add">
                    <Order>2</Order>
                    <Path>reg add "HKLM\SYSTEM\Setup\LabConfig" /v BypassRAMCheck /t REG_DWORD /d 1 /f</Path>
                </RunSynchronousCommand>
                <RunSynchronousCommand wcm:action="add">
                    <Order>3</Order>
                    <Path>reg add "HKLM\SYSTEM\Setup\LabConfig" /v BypassSecureBootCheck /t REG_DWORD /d 1 /f</Path>
                </RunSynchronousCommand>
                <RunSynchronousCommand wcm:action="add">
                    <Order>4</Order>
                    <Path>reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\OOBE" /v BypassNRO /t REG_DWORD /d 1 /f</Path>
                </RunSynchronousCommand>
            </RunSynchronous>
        </component>
    </settings>
    <settings pass="oobeSystem">
        <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <ComputerName>{computer_name}</ComputerName>
            <TimeZone>{timezone}</TimeZone>
            <OOBE>
                <HideEULAPage>true</HideEULAPage>
                <HideOEMRegistrationScreen>true</HideOEMRegistrationScreen>
                <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
                <HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE>
                <NetworkLocation>Work</NetworkLocation>
                <ProtectYourPC>3</ProtectYourPC>
                <SkipMachineOOBE>{'true' if skip_oobe else 'false'}</SkipMachineOOBE>
                <SkipUserOOBE>{'true' if skip_oobe else 'false'}</SkipUserOOBE>
            </OOBE>
            <UserAccounts>
                <LocalAccounts>
                    <LocalAccount wcm:action="add">
                        <Name>{username}</Name>
                        <Group>Administrators</Group>
                        <DisplayName>{username}</DisplayName>
                        <Password>
                            <Value>{password}</Value>
                            <PlainText>true</PlainText>
                        </Password>
                    </LocalAccount>
                </LocalAccounts>
            </UserAccounts>
            {'<AutoLogon><Enabled>true</Enabled><Username>' + username + '</Username><Password><Value>' + password + '</Value><PlainText>true</PlainText></Password></AutoLogon>' if auto_logon else ''}
        </component>
    </settings>
</unattend>
"""
        return xml_template

    def save_to_file(self, target_path: str) -> str:
        """
        Saves autounattend.xml file to specified path.
        """
        target_path = os.path.abspath(target_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        xml_content = self.generate_xml()
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        return target_path
