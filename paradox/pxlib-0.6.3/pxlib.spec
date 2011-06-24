Summary: A library to read Paradox DB files
Name: pxlib
Version: 0.6.3
Release: 1
License: see doc/COPYING
Group: Applications/Utils
Url: http://pxlib.sourceforge.net/
Packager: Uwe Steinmann <uwe@steinmann.cx>
Source: http://prdownloads.sourceforge.net/pxlib/pxlib-%{PACKAGE_VERSION}.tar.gz
BuildRoot: /var/tmp/rpm/pxlib-root
Prefix: /usr/local

%description
pxlib is a simply and still small C library to read Paradox DB files. It
supports all versions starting from 3.0. It currently has a very limited set of
functions like to open a DB file, read its header and read every single record.

%package devel
Summary: A library to read Paradox DB files (Development)
Group: Development/Libraries
Requires: pxlib = %{version}

%description devel
pxlib is a simply and still small C library to read Paradox DB files. It
supports all versions starting from 3.0. It currently has a very limited set of
functions like to open a DB file, read its header and read every single record.

%prep
%setup

%build
./configure --prefix=%prefix --with-sqlite --with-gsf --mandir=%prefix/share/man --infodir=%prefix/share/info
make

%install
rm -rf ${RPM_BUILD_ROOT}
install -d -m 755 ${RPM_BUILD_ROOT}
make DESTDIR=${RPM_BUILD_ROOT} install

%clean
rm -rf ${RPM_BUILD_ROOT}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%attr(-,root,root) %doc README AUTHORS ChangeLog COPYING INSTALL
%attr(-,root,root) %{prefix}/lib/lib*.so.*
%attr(-,root,root) %{prefix}/share/locale/*/LC_MESSAGES/*

%files devel
%attr(-,root,root) %{prefix}/lib/lib*.so
%attr(-,root,root) %{prefix}/lib/*.a
%attr(-,root,root) %{prefix}/lib/*.la
%attr(-,root,root) %{prefix}/lib/pkgconfig/*
%attr(-,root,root) %{prefix}/include/*
%attr(-,root,root) %{prefix}/share/man/man3/*
