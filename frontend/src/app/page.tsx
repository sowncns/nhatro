import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <main className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-12">
        <div className="max-w-3xl">
          <p className="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">
            SaaS bán cho chủ trọ
          </p>
          <h1 className="mt-6 text-4xl font-extrabold tracking-normal text-slate-950 sm:text-6xl">
            Chủ trọ tự động quản lý nhà trọ sau khi mua gói dịch vụ
          </h1>
          <p className="mt-5 text-lg leading-8 text-slate-600">
            NhaTro giúp chủ trọ thêm khu/phòng, quản lý khách thuê, tự tạo hóa đơn, QR thanh toán, nhắc nợ, cảnh báo hợp đồng và theo dõi doanh thu trong một dashboard.
          </p>
        </div>

        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            href="/register"
            className="rounded-xl bg-slate-950 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-slate-800"
          >
            Chủ trọ đăng ký dùng thử
          </Link>
          <Link
            href="/login"
            className="rounded-xl bg-white px-6 py-3 text-base font-semibold text-slate-900 shadow-sm ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
          >
            Đăng nhập Chủ Trọ
          </Link>
          <Link
            href="/portal/login"
            className="rounded-xl bg-white px-6 py-3 text-base font-semibold text-blue-700 shadow-sm ring-1 ring-inset ring-blue-200 hover:bg-blue-50"
          >
            Đăng nhập Người Thuê
          </Link>
          <Link
            href="/billing"
            className="rounded-xl bg-white px-6 py-3 text-base font-semibold text-emerald-700 shadow-sm ring-1 ring-inset ring-emerald-200 hover:bg-emerald-50"
          >
            Xem gói dịch vụ
          </Link>
        </div>

        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {['Tự động tạo hóa đơn hàng tháng', 'Chủ trọ mua module bằng thanh toán', 'Admin hệ thống quản lý gói và giao dịch'].map((item) => (
            <div key={item} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="text-sm font-semibold text-slate-900">{item}</div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
