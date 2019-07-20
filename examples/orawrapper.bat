@echo off
REM Wraps oracle driver path variables
REM What was necessary to get this to work? https://oracle.github.io/odpi/doc/installation.html#windows
REM  1. (maybe optional) Install MS C++ 2013 64 bit Redistributable: https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads#bookmark-vs2013
REM  2. Install Oracle Instant Client 64 bit 18.5 base package:      https://www.oracle.com/technetwork/topics/winx64soft-089540.html

SET PATH=C:\Oracle\instantclient_18_5;%PATH%
SET LAUNCHPAD_CFG=.\tree_cfg.yml
echo Don't forget to set env vars like XOB10_USER, XOB10_PW...
%*
