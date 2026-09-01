Name:           msmtp
Version:        1.8.33
Release:        1%{?dist}
Summary:        SMTP client with sendmail compatible interface

License:        GPLv3+
URL:            https://marlam.de/msmtp
Source0:        https://marlam.de/msmtp/releases/%{name}-%{version}.tar.xz

BuildRequires:  gcc, make, gnutls-devel

%description
msmtp is an SMTP client that can be used to send mail from
a command line, similar to sendmail. It supports TLS/SSL,
multiple accounts, and various authentication methods.
%prep
%setup -q
%build

CFLAGS="%{optflags} -include stdbool.h"
%configure
%make_build
%install
%make_install
%find_lang %{name}
rm -f %{buildroot}%{_infodir}/dir
%files -f %{name}.lang
%license COPYING
%doc AUTHORS NEWS README
%{_bindir}/msmtp
%{_bindir}/msmtpd
%{_mandir}/man1/msmtp.1*
%{_mandir}/man1/msmtpd.1*
%{_infodir}/msmtp.info*