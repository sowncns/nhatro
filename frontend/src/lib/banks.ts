export interface Bank {
  id: number
  name: string
  code: string
  bin: string
  shortName: string
  logo: string
}

export const FALLBACK_BANKS: Bank[] = [
  { id: 1, name: "Ngân hàng TMCP Ngoại thương Việt Nam", code: "VCB", bin: "970436", shortName: "Vietcombank", logo: "https://cdn.vietqr.io/img/VCB.png" },
  { id: 2, name: "Ngân hàng TMCP Công thương Việt Nam", code: "CTG", bin: "970415", shortName: "VietinBank", logo: "https://cdn.vietqr.io/img/ICB.png" },
  { id: 3, name: "Ngân hàng TMCP Đầu tư và Phát triển Việt Nam", code: "BIDV", bin: "970418", shortName: "BIDV", logo: "https://cdn.vietqr.io/img/BIDV.png" },
  { id: 4, name: "Ngân hàng Nông nghiệp và Phát triển Nông thôn Việt Nam", code: "VBA", bin: "970405", shortName: "Agribank", logo: "https://cdn.vietqr.io/img/VBA.png" },
  { id: 5, name: "Ngân hàng TMCP Quân đội", code: "MB", bin: "970422", shortName: "MBBank", logo: "https://cdn.vietqr.io/img/MB.png" },
  { id: 6, name: "Ngân hàng TMCP Kỹ thương Việt Nam", code: "TCB", bin: "970407", shortName: "Techcombank", logo: "https://cdn.vietqr.io/img/TCB.png" },
  { id: 7, name: "Ngân hàng TMCP Á Châu", code: "ACB", bin: "970416", shortName: "ACB", logo: "https://cdn.vietqr.io/img/ACB.png" },
  { id: 8, name: "Ngân hàng TMCP Việt Nam Thịnh Vượng", code: "VPB", bin: "970432", shortName: "VPBank", logo: "https://cdn.vietqr.io/img/VPB.png" },
  { id: 9, name: "Ngân hàng TMCP Tiên Phong", code: "TPB", bin: "970423", shortName: "TPBank", logo: "https://cdn.vietqr.io/img/TPB.png" },
  { id: 10, name: "Ngân hàng TMCP Sài Gòn Thương Tín", code: "STB", bin: "970403", shortName: "Sacombank", logo: "https://cdn.vietqr.io/img/STB.png" },
]

export async function getBanks(): Promise<Bank[]> {
  try {
    const response = await fetch('https://api.vietqr.io/v2/banks')
    const json = await response.json()
    if (json.code === '00' && Array.isArray(json.data)) {
      return json.data
    }
    return FALLBACK_BANKS
  } catch (error) {
    console.error('Failed to fetch banks:', error)
    return FALLBACK_BANKS
  }
}
